from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Skill

logger = logging.getLogger(__name__)

GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"
GROQ_TIMEOUT_SECONDS = 8.0

EMPTY_PROFILE: dict[str, Any] = {
    "skills": [],
    "education": {"degree": None, "institution": None, "field": None, "year_of_study": None},
    "projects": [],
    "certificates": [],
}


def _clean_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalise_profile(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    skills = payload.get("skills", [])
    education = payload.get("education", {})
    projects = payload.get("projects", [])
    certificates = payload.get("certificates", [])
    if not isinstance(skills, list) or not isinstance(education, dict):
        return None
    if not isinstance(projects, list) or not isinstance(certificates, list):
        return None

    clean_skills: list[str] = []
    for skill in skills:
        value = _clean_string(skill)
        if value and value.casefold() not in {item.casefold() for item in clean_skills}:
            clean_skills.append(value)

    clean_projects = []
    for project in projects:
        if isinstance(project, dict):
            title = _clean_string(project.get("title")) or "Project"
            description = _clean_string(project.get("description")) or ""
            if description:
                clean_projects.append({"title": title, "description": description})

    clean_certificates = []
    for certificate in certificates:
        if isinstance(certificate, dict):
            name = _clean_string(certificate.get("name"))
            if name:
                clean_certificates.append(
                    {
                        "name": name,
                        "issuing_organization": _clean_string(certificate.get("issuing_organization")),
                    }
                )

    year = education.get("year_of_study")
    if not isinstance(year, int):
        year = None
    return {
        "skills": clean_skills,
        "education": {
            "degree": _clean_string(education.get("degree")),
            "institution": _clean_string(education.get("institution")),
            "field": _clean_string(education.get("field")),
            "year_of_study": year,
        },
        "projects": clean_projects,
        "certificates": clean_certificates,
    }


def _section_lines(text: str, section_names: set[str]) -> list[str]:
    lines = [line.strip() for line in text.splitlines()]
    header_pattern = re.compile(r"^[A-Za-z][A-Za-z &/+-]{1,50}:?$", re.IGNORECASE)
    active = False
    output: list[str] = []
    for line in lines:
        normalized = re.sub(r"[^a-z]", "", line.casefold())
        if normalized in section_names:
            active = True
            continue
        if active and line and header_pattern.match(line):
            possible_header = re.sub(r"[^a-z]", "", line.casefold())
            if possible_header in {
                "experience", "workexperience", "education", "skills", "projects", "academicprojects",
                "personalprojects", "certifications", "certificates", "summary", "objective", "achievements",
            }:
                break
        if active and line:
            output.append(line)
    return output


def _rule_based_extract(text: str, db: Session) -> dict[str, Any]:
    """Best-effort fallback; project/certificate sections remain raw blocks by design."""
    skills: list[str] = []
    all_skills = db.scalars(select(Skill).order_by(Skill.id)).all()
    lowered = text.casefold()
    for skill in all_skills:
        candidates = [skill.name, *(skill.aliases or [])]
        def mentioned(candidate: str) -> bool:
            candidate = candidate.strip()
            if not candidate:
                return False
            if len(candidate) <= 2:
                return re.search(rf"(?<![a-z0-9]){re.escape(candidate.casefold())}(?![a-z0-9])", lowered) is not None
            return candidate.casefold() in lowered

        if any(mentioned(candidate) for candidate in candidates):
            if skill.name.casefold() not in {item.casefold() for item in skills}:
                skills.append(skill.name)

    degree_patterns = [
        r"B\.?\s*Tech\.?", r"B\.?\s*E\.?", r"B\.?\s*Sc\.?", r"M\.?\s*Tech\.?", r"M\.?\s*E\.?",
        r"M\.?\s*Sc\.?", r"BBA", r"B\.?\s*Com\.?", r"MBA", r"MCA", r"BCA",
    ]
    degree = None
    for pattern in degree_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            degree = re.sub(r"\s+", " ", match.group(0)).strip()
            break
    institution_match = re.search(r"(?im)^.*(?:university|institute|college).*$", text)
    field_match = re.search(r"(?im)^(?:field|major|speciali[sz]ation)\s*:\s*(.+)$", text)
    if field_match is None:
        field_match = re.search(r"(?im)^(?:[^\n]*degree[^\n]*|(?:B|M)\.?\s*(?:Tech|E|Sc|BA|BA|Com|CA|BA)\.?)\s+in\s+([^\n]+)$", text)
    year_match = re.search(r"(?i)\byear(?:\s+of\s+study)?\s*[:\-]?\s*([1-9])\b", text)
    education = {
        "degree": degree,
        "institution": institution_match.group(0).strip() if institution_match else None,
        "field": field_match.group(1).strip() if field_match else None,
        "year_of_study": int(year_match.group(1)) if year_match else None,
    }

    projects = [{"title": "Project", "description": line} for line in _section_lines(text, {"projects", "academicprojects", "personalprojects"})]
    certificates = [
        {"name": line, "issuing_organization": None}
        for line in _section_lines(text, {"certifications", "certificates"})
    ]
    profile = _normalise_profile({"skills": skills, "education": education, "projects": projects, "certificates": certificates})
    assert profile is not None
    return profile


def _resume_prompt(resume_text: str) -> str:
    return f"""Extract a resume into exactly one JSON object. Return ONLY valid JSON, with no markdown and no extra keys, using exactly this shape:
{{"skills":["Python"],"education":{{"degree":"...","institution":"...","field":"...","year_of_study":3}},"projects":[{{"title":"...","description":"..."}}],"certificates":[{{"name":"...","issuing_organization":"..."}}]}}
Use null for unknown education values and [] for sections not present. Only include skills explicitly supported by the resume text; do not infer skills from job titles or projects unless the skill is clearly stated.

RESUME TEXT:
{resume_text}
"""


def _llm_extract(resume_text: str) -> dict[str, Any]:
    if not settings.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not configured")
    body = {
        "model": GROQ_MODEL,
        "temperature": 0.0,
        "max_completion_tokens": 1000,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": "You extract only explicit resume facts. Respond with valid JSON matching the requested shape.",
            },
            {"role": "user", "content": _resume_prompt(resume_text)},
        ],
    }
    logger.info("Resume Groq extraction attempt: key_configured=%s model=%s", bool(settings.GROQ_API_KEY), GROQ_MODEL)
    response = httpx.post(
        GROQ_ENDPOINT,
        headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
        json=body,
        timeout=GROQ_TIMEOUT_SECONDS,
    )
    logger.info("Resume Groq extraction response: status_code=%s", response.status_code)
    if response.is_error:
        logger.error("Resume Groq API error: status_code=%s body=%s", response.status_code, response.text[:4000])
    response.raise_for_status()
    payload = response.json()
    choice = payload.get("choices", [{}])[0]
    content = choice.get("message", {}).get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError(f"Groq returned empty resume extraction (finish_reason={choice.get('finish_reason')})")
    parsed = json.loads(content)
    normalised = _normalise_profile(parsed)
    if normalised is None:
        raise ValueError("Groq resume extraction did not match the required JSON shape")
    return normalised


def extract_resume_profile(resume_text: str, db: Session) -> tuple[dict[str, Any], str]:
    try:
        profile = _llm_extract(resume_text)
        logger.info("Resume extraction completed: method=llm")
        return profile, "llm"
    except Exception as exc:
        logger.warning(
            "Resume Groq extraction unavailable; using rule_based fallback: exception_type=%s message=%s",
            type(exc).__name__, exc,
        )
        profile = _rule_based_extract(resume_text, db)
        logger.info("Resume extraction completed: method=rule_based")
        return profile, "rule_based"


__all__ = ["extract_resume_profile"]
