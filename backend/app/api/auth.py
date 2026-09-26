from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Student
from app.api.students import full_student_json, load_full_student

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> dict:
    email = payload.email.strip().lower()
    student = db.scalar(select(Student).where(Student.email.ilike(email)))
    if student is None:
        raise HTTPException(
            status_code=404,
            detail="No account found with this email — try signing up instead",
        )
    return full_student_json(load_full_student(db, student.id))


__all__ = ["router"]
