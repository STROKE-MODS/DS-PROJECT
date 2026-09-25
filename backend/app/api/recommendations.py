from __future__ import annotations

from functools import lru_cache
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import SessionLocal, get_db
from app.models import CareerPath, Internship, InternshipSkill, Recommendation, Student, StudentSkill
from app.nlp.explanation import generate_explanation
from app.recommendation.engine import Profile, profile_from_student, recommend
from app.recommendation.personalization import build_personalization_policy
from app.recommendation.preparation import enrich_result

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@lru_cache(maxsize=1)
def cached_internships() -> tuple[Internship, ...]:
    """Load all recommendation inputs once; embeddings remain process-local thereafter."""
    with SessionLocal() as session:
        return tuple(session.scalars(
            select(Internship)
            .options(
                selectinload(Internship.skills).selectinload(InternshipSkill.skill),
                selectinload(Internship.career_path).selectinload(CareerPath.next_step),
                selectinload(Internship.career_path).selectinload(CareerPath.previous_steps),
            )
            .order_by(Internship.id)
        ).all())


class AdHocProfile(BaseModel):
    skills: list[str] = Field(default_factory=list)
    year_of_study: int | None = None
    location: str | None = None
    interests: list[str] = Field(default_factory=list)
    preferences: dict[str, Any] = Field(default_factory=dict)
    career_goal_id: int | None = None


class RecommendationRequest(BaseModel):
    student_id: int | None = None
    profile: AdHocProfile | None = None
    limit: int = Field(default=5, ge=1, le=20)


def internship_json(internship: Internship) -> dict[str, Any]:
    return {
        "id": internship.id, "title": internship.title, "company": internship.company,
        "description": internship.description, "sector": internship.sector,
        "education_required": internship.education_required, "min_year": internship.min_year,
        "location": internship.location, "work_mode": internship.work_mode.value if internship.work_mode else None,
        "duration": internship.duration, "stipend": internship.stipend,
        "experience_required": internship.experience_required, "career_path_id": internship.career_path_id,
        "is_demo_data": internship.is_demo_data,
    }


def response_json(result: dict[str, Any]) -> dict[str, Any]:
    detail = result["_skill_detail"]
    return {
        "internship": internship_json(result["internship"]),
        "match_score": result["match_score"], "readiness_score": result["readiness_score"],
        "status": result["status"].value,
        "score_breakdown": result["score_breakdown"],
        "why_recommended": result["why_recommended"],
        "matched_skills": detail["matched_skills"],
        "missing_critical_skills": detail["missing_critical_skills"],
        "missing_important_skills": detail["missing_important_skills"],
        "optional_skills": result["optional_skills"],
        "preparation_plan": result["preparation_plan"],
        "personalization_adjustments": result.get("personalization_adjustments", []),
    }


@router.post("")
def create_recommendations(payload: RecommendationRequest, db: Session = Depends(get_db)) -> dict[str, list[dict[str, Any]]]:
    if (payload.student_id is None) == (payload.profile is None):
        raise HTTPException(status_code=400, detail="Provide exactly one of student_id or profile")

    student = None
    if payload.student_id is not None:
        student = db.scalar(
            select(Student)
            .options(
                selectinload(Student.skills).selectinload(StudentSkill.skill),
                selectinload(Student.career_goal),
            )
            .where(Student.id == payload.student_id)
        )
        if student is None:
            raise HTTPException(status_code=404, detail="Student not found")
        profile = profile_from_student(student)
        personalization = build_personalization_policy(student.id, db)
    else:
        profile = Profile(**payload.profile.model_dump())
        personalization = None

    internships = cached_internships()
    results = recommend(profile, internships, payload.limit, personalization=personalization)

    if student is not None:
        existing_rows = db.scalars(
            select(Recommendation)
            .where(
                Recommendation.student_id == student.id,
                Recommendation.internship_id.in_([result["internship"].id for result in results]),
            )
            .order_by(Recommendation.created_at.desc(), Recommendation.id.desc())
        ).all()
        existing_by_internship: dict[int, Recommendation] = {}
        for row in existing_rows:
            existing_by_internship.setdefault(row.internship_id, row)
        for result in results:
            existing = existing_by_internship.get(result["internship"].id)
            if existing is not None and existing.explanation_text:
                result["why_recommended"] = existing.explanation_text
                continue
            result["why_recommended"] = generate_explanation(
                result["internship"], result["match_score"], result["status"].value,
                result["_skill_detail"]["matched_skills"],
                result["_skill_detail"]["missing_critical_skills"],
                result["_skill_detail"]["missing_important_skills"], result["score_breakdown"],
            )
            if existing is not None:
                existing.explanation_text = result["why_recommended"]
            else:
                db.add(Recommendation(
                    student_id=student.id,
                    internship_id=result["internship"].id,
                    match_score=result["match_score"],
                    readiness_score=result["readiness_score"],
                    status=result["status"],
                    score_breakdown=result["score_breakdown"],
                    explanation_text=result["why_recommended"],
                ))
        db.commit()
    else:
        for result in results:
            result["why_recommended"] = generate_explanation(
                result["internship"], result["match_score"], result["status"].value,
                result["_skill_detail"]["matched_skills"],
                result["_skill_detail"]["missing_critical_skills"],
                result["_skill_detail"]["missing_important_skills"], result["score_breakdown"],
            )

    for result in results:
        enrich_result(
            result,
            profile,
            internships,
            db=db if student is not None else None,
            student_id=student.id if student is not None else None,
        )
    if student is not None:
        db.commit()

    return {"recommendations": [response_json(result) for result in results]}
