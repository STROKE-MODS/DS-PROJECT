from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models import CareerPath, Student

router = APIRouter(prefix="/api/students", tags=["students"])


class CareerGoalUpdate(BaseModel):
    career_goal_id: int | None


class StudentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=3, max_length=255)
    education_level: str | None = None
    degree: str | None = None
    branch: str | None = None
    year_of_study: int | None = Field(default=None, ge=1, le=10)
    location: str | None = None


class StudentProfileUpdate(BaseModel):
    education_level: str | None = None
    degree: str | None = None
    branch: str | None = None
    year_of_study: int | None = Field(default=None, ge=1, le=10)
    location: str | None = None


def full_student_json(student: Student) -> dict:
    return {
        "id": student.id,
        "name": student.name,
        "email": student.email,
        "education_level": student.education_level,
        "degree": student.degree,
        "branch": student.branch,
        "year_of_study": student.year_of_study,
        "location": student.location,
        "interests": student.interests or [],
        "preferences": student.preferences or {},
        "career_goal_id": student.career_goal_id,
        "skills": [link.skill.name for link in student.skills],
        "certificates": [
            {"name": certificate.name, "issuing_organization": certificate.issuing_organization}
            for certificate in student.certificates
        ],
        "projects": student.projects or [],
        "resume_text_saved": bool(student.resume_text),
        "resume_file_path": student.resume_file_path,
    }


def load_full_student(db: Session, student_id: int) -> Student:
    student = db.scalar(
        select(Student)
        .options(
            selectinload(Student.skills),
            selectinload(Student.certificates),
        )
        .where(Student.id == student_id)
    )
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.post("", status_code=status.HTTP_201_CREATED)
def create_student(payload: StudentCreate, db: Session = Depends(get_db)) -> dict:
    email = str(payload.email).strip().lower()
    existing = db.scalar(select(Student).where(Student.email.ilike(email)))
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists — try logging in instead",
        )
    student = Student(
        name=payload.name.strip(),
        email=email,
        education_level=payload.education_level,
        degree=payload.degree,
        branch=payload.branch,
        year_of_study=payload.year_of_study,
        location=payload.location,
    )
    db.add(student)
    db.commit()
    return full_student_json(load_full_student(db, student.id))


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


@router.patch("/{student_id}")
def update_student_profile(
    student_id: int,
    payload: StudentProfileUpdate,
    db: Session = Depends(get_db),
) -> dict:
    student = load_full_student(db, student_id)
    for field_name, value in payload.model_dump(exclude_unset=True).items():
        setattr(student, field_name, value)
    db.commit()
    return full_student_json(load_full_student(db, student_id))
