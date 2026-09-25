from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import CareerPath, Student

router = APIRouter(prefix="/api/students", tags=["students"])


class CareerGoalUpdate(BaseModel):
    career_goal_id: int | None


@router.get("")
def list_students(db: Session = Depends(get_db)) -> list[dict]:
    students = db.query(Student).order_by(Student.id).all()
    return [
        {
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "education_level": student.education_level,
            "degree": student.degree,
            "branch": student.branch,
            "year_of_study": student.year_of_study,
            "location": student.location,
            "career_goal_id": student.career_goal_id,
        }
        for student in students
    ]


@router.patch("/{student_id}/career-goal")
def update_career_goal(
    student_id: int,
    payload: CareerGoalUpdate,
    db: Session = Depends(get_db),
) -> dict:
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    if payload.career_goal_id is not None:
        career_path = db.get(CareerPath, payload.career_goal_id)
        if career_path is None:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid career_goal_id: {payload.career_goal_id}",
            )

    student.career_goal_id = payload.career_goal_id
    db.commit()
    db.refresh(student)
    return {
        "id": student.id,
        "name": student.name,
        "email": student.email,
        "education_level": student.education_level,
        "degree": student.degree,
        "branch": student.branch,
        "year_of_study": student.year_of_study,
        "location": student.location,
        "career_goal_id": student.career_goal_id,
    }
