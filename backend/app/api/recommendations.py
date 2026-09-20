from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models import Internship, InternshipSkill, Recommendation, Student, StudentSkill
from app.recommendation.engine import Profile, profile_from_student, recommend

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


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
    return {
        "internship": internship_json(result["internship"]),
        "match_score": result["match_score"], "readiness_score": result["readiness_score"],
        "status": result["status"].value,
        "score_breakdown": result["score_breakdown"],
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
    else:
        profile = Profile(**payload.profile.model_dump())

    internships = db.scalars(
        select(Internship)
        .options(
            selectinload(Internship.skills).selectinload(InternshipSkill.skill),
        )
        .order_by(Internship.id)
    ).all()
    results = recommend(profile, internships, payload.limit)

    if student is not None:
        for result in results:
            db.add(Recommendation(
                student_id=student.id,
                internship_id=result["internship"].id,
                match_score=result["match_score"],
                readiness_score=result["readiness_score"],
                status=result["status"],
                score_breakdown=result["score_breakdown"],
            ))
        db.commit()

    return {"recommendations": [response_json(result) for result in results]}
