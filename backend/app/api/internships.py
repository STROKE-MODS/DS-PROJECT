from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Internship

router = APIRouter(prefix="/api/internships", tags=["internships"])


@router.get("")
def list_internships(db: Session = Depends(get_db)) -> list[dict]:
    internships = db.query(Internship).order_by(Internship.id).all()
    return [
        {
            "id": internship.id,
            "title": internship.title,
            "company": internship.company,
            "description": internship.description,
            "sector": internship.sector,
            "education_required": internship.education_required,
            "min_year": internship.min_year,
            "location": internship.location,
            "work_mode": internship.work_mode.value if internship.work_mode else None,
            "duration": internship.duration,
            "stipend": internship.stipend,
            "experience_required": internship.experience_required,
            "career_path_id": internship.career_path_id,
            "is_demo_data": internship.is_demo_data,
        }
        for internship in internships
    ]
