from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"


def _names(items: list[dict[str, str]]) -> str:
    return ", ".join(item["skill_name"] for item in items) or "none"


def template_explanation(
    internship: Any,
    score: float,
    status: str,
    matched_skills: list[dict[str, str]],
    missing_critical_skills: list[str],
    missing_important_skills: list[str],
    score_breakdown: dict[str, dict[str, float]],
) -> str:
    matched = _names(matched_skills)
    critical = ", ".join(missing_critical_skills) or "none"
    important = ", ".join(missing_important_skills) or "none"
    reasons: list[str] = []
    if matched_skills:
        reasons.append(f"your matched skills include {matched}")
    if score_breakdown.get("career_alignment", {}).get("raw", 0) > 0:
        reasons.append("it aligns with your career direction")
    if score_breakdown.get("location_match", {}).get("raw", 0) > 0:
        reasons.append("its location or work mode fits your preferences")
    reason_text = "; ".join(reasons) or "its overall profile is a reasonable starting point"
    improvement = f" To become a stronger candidate, build {critical} first"
    if not missing_critical_skills and missing_important_skills:
        improvement = f" You could further strengthen your application with {important}"
    elif not missing_critical_skills and not missing_important_skills:
        improvement = " You already cover the listed skill requirements"
    return f"This {internship.sector or 'internship'} recommendation scored {score:.1f} ({status}) because {reason_text}.{improvement}."


def build_prompt(
    internship: Any,
    score: float,
    status: str,
    matched_skills: list[dict[str, str]],
    missing_critical_skills: list[str],
    missing_important_skills: list[str],
    score_breakdown: dict[str, dict[str, float]],
) -> str:
    return f"""Write one or two concise sentences explaining why this internship was recommended.
Use only the facts supplied below. Do not invent experience, achievements, company details, or skills.
Mention matched skills accurately; semantic matches are related skills, not exact matches. If critical skills are missing, say what the student should build to become stronger.

Internship: {internship.title} at {internship.company}
Sector: {internship.sector or 'not specified'}
Final match score: {score:.1f}
Status: {status}
Matched skills: {matched_skills or 'none'}
Missing critical skills: {missing_critical_skills or 'none'}
Missing important skills: {missing_important_skills or 'none'}
Career alignment raw score: {score_breakdown.get('career_alignment', {}).get('raw', 0)}
Location match raw score: {score_breakdown.get('location_match', {}).get('raw', 0)}
Preference match raw score: {score_breakdown.get('preference_match', {}).get('raw', 0)}
"""


def _groq_explanation(prompt: str) -> str:
    key_configured = bool(settings.GROQ_API_KEY)
    logger.info("Groq explanation attempt: key_configured=%s", key_configured)
    if not key_configured:
        raise RuntimeError("GROQ_API_KEY is not configured")
    request_body = {
        "model": GROQ_MODEL,
        "temperature": 0.2,
        "max_completion_tokens": 350,
        "messages": [
            {"role": "system", "content": "You write concise, factual internship recommendation explanations."},
            {"role": "user", "content": prompt},
        ],
    }
    try:
        response = httpx.post(
            GROQ_ENDPOINT,
            headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
            json=request_body,
            timeout=5.0,
        )
        logger.info("Groq explanation response: status_code=%s", response.status_code)
        if response.is_error:
            logger.error("Groq API error response: status_code=%s body=%s", response.status_code, response.text[:4000])
        response.raise_for_status()
        payload = response.json()
        choice = payload.get("choices", [{}])[0]
        message = choice.get("message", {})
        content = message.get("content")
        finish_reason = choice.get("finish_reason")
        content_present = isinstance(content, str) and bool(content.strip())
        logger.info("Groq explanation completion: finish_reason=%s content_present=%s", finish_reason, content_present)
        if not isinstance(content, str) or not content.strip():
            raise ValueError(f"Groq returned empty explanation (finish_reason={finish_reason})")
        return content.strip()
    except Exception as exc:
        logger.exception("Groq explanation request failed: exception_type=%s message=%s", type(exc).__name__, exc)
        raise


def generate_explanation(
    internship: Any,
    score: float,
    status: str,
    matched_skills: list[dict[str, str]],
    missing_critical_skills: list[str],
    missing_important_skills: list[str],
    score_breakdown: dict[str, dict[str, float]],
) -> str:
    fallback = template_explanation(
        internship, score, status, matched_skills,
        missing_critical_skills, missing_important_skills, score_breakdown,
    )
    try:
        return _groq_explanation(build_prompt(
            internship, score, status, matched_skills,
            missing_critical_skills, missing_important_skills, score_breakdown,
        ))
    except Exception as exc:  # fallback must shield the API from all provider failures
        logger.warning("Groq explanation unavailable; using template fallback: exception_type=%s message=%s", type(exc).__name__, exc)
        return fallback
