from __future__ import annotations

import logging
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models import Certificate, Skill, Student, StudentSkill
from app.models.enums import SkillSource
from app.resume.extraction import extract_pdf_bytes
from app.resume.parser import extract_resume_profile

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/students", tags=["resume"])
UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads" / "resumes"


class EducationDraft(BaseModel):
    degree: str | None = None
    institution: str | None = None
    field: str | None = None
    year_of_study: int | None = Field(default=None, ge=1, le=10)


class ProjectDraft(BaseModel):
    title: str
    description: str


class CertificateDraft(BaseModel):
    name: str
    issuing_organization: str | None = None


class ResumeDraftProfile(BaseModel):
    skills: list[str] = Field(default_factory=list)
    education: EducationDraft = Field(default_factory=EducationDraft)
    projects: list[ProjectDraft] = Field(default_factory=list)
    certificates: list[CertificateDraft] = Field(default_factory=list)


def _student_or_404(db: Session, student_id: int) -> Student:
    student = db.scalar(
        select(Student)
        .options(selectinload(Student.skills).selectinload(StudentSkill.skill), selectinload(Student.certificates))
        .where(Student.id == student_id)
    )
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


def _profile_json(student: Student) -> dict:
    return {
        "id": student.id,
        "name": student.name,
        "email": student.email,
        "degree": student.degree,
        "branch": student.branch,
        "year_of_study": student.year_of_study,
        "projects": student.projects or [],
        "skills": [link.skill.name for link in student.skills],
        "certificates": [
            {"name": certificate.name, "issuing_organization": certificate.issuing_organization}
            for certificate in student.certificates
        ],
        "resume_text_saved": bool(student.resume_text),
        "resume_file_path": student.resume_file_path,
    }


def _find_skill_by_name_or_alias(skills: list[Skill], requested: str) -> Skill | None:
    normalized = requested.strip().casefold()
    for skill in skills:
        if skill.name.casefold() == normalized or any(alias.casefold() == normalized for alias in (skill.aliases or [])):
            return skill
    return None


@router.post("/{student_id}/resume/upload")
async def upload_resume(
    student_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict:
    student = _student_or_404(db, student_id)
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported")
    pdf_bytes = await file.read()
    if not pdf_bytes.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid PDF")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"student_{student_id}_{uuid4().hex}.pdf"
    destination = UPLOAD_DIR / filename
    destination.write_bytes(pdf_bytes)
    relative_path = str(destination.relative_to(Path(__file__).resolve().parents[2]))

    try:
        resume_text = extract_pdf_bytes(pdf_bytes)
        student.resume_text = resume_text
        student.resume_file_path = relative_path
        db.commit()
        profile, extraction_method = extract_resume_profile(resume_text, db)
    except Exception:
        db.rollback()
        destination.unlink(missing_ok=True)
        logger.exception("Resume upload failed for student_id=%s", student_id)
        raise HTTPException(status_code=400, detail="Could not extract text from the uploaded PDF")

    return {
        "resume_text_preview": resume_text[:500],
        "extraction_method": extraction_method,
        "draft_profile": profile,
    }


@router.post("/{student_id}/resume/confirm")
def confirm_resume(
    student_id: int,
    draft: ResumeDraftProfile,
    db: Session = Depends(get_db),
) -> dict:
    student = _student_or_404(db, student_id)
    known_skills = db.scalars(select(Skill).order_by(Skill.id)).all()
    existing_skill_ids = {link.skill_id for link in student.skills}
    confirmed_skills: list[Skill] = []
    for requested in draft.skills:
        skill = _find_skill_by_name_or_alias(known_skills, requested)
        if skill is None:
            skill = Skill(name=requested.strip(), category="resume_confirmed", aliases=[])
            db.add(skill)
            db.flush()
            known_skills.append(skill)
        if skill.id not in existing_skill_ids:
            db.add(StudentSkill(student_id=student.id, skill_id=skill.id, proficiency=None, source=SkillSource.resume_extracted))
            existing_skill_ids.add(skill.id)
        confirmed_skills.append(skill)

    education = draft.education
    if education.degree is not None:
        student.degree = education.degree
    if education.field is not None:
        student.branch = education.field
    if education.year_of_study is not None:
        student.year_of_study = education.year_of_study
    student.projects = [project.model_dump() for project in draft.projects]

    existing_certificates = {
        (certificate.name.casefold(), (certificate.issuing_organization or "").casefold())
        for certificate in student.certificates
    }
    for certificate in draft.certificates:
        key = (certificate.name.casefold(), (certificate.issuing_organization or "").casefold())
        if key in existing_certificates:
            continue
        db.add(
            Certificate(
                student_id=student.id,
                name=certificate.name,
                issuing_organization=certificate.issuing_organization,
                extracted_from_resume=True,
            )
        )
        existing_certificates.add(key)

    db.commit()
    refreshed = _student_or_404(db, student_id)
    return {"student": _profile_json(refreshed)}


__all__ = ["router"]
