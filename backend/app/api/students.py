from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Student

router = APIRouter(prefix="/api/students", tags=["students"])


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
