from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Internship, WorkMode

router = APIRouter(prefix="/api/internships", tags=["internships"])


@router.get("")
def list_internships(
    sector: str | None = None,
    location: str | None = None,
    work_mode: WorkMode | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    query = db.query(Internship)
    if sector:
        query = query.filter(Internship.sector == sector)
    if location:
        query = query.filter(Internship.location.ilike(f"%{location}%"))
    if work_mode:
        query = query.filter(Internship.work_mode == work_mode)

    total = query.with_entities(func.count(Internship.id)).scalar() or 0
    internships = query.order_by(Internship.id).offset((page - 1) * page_size).limit(page_size).all()
    items = [
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
    return {"items": items, "total": total, "page": page, "page_size": page_size}
