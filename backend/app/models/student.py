from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ProficiencyLevel, SkillSource

if TYPE_CHECKING:
    from app.models.career_path import CareerPath
    from app.models.internship import Internship
    from app.models.recommendation import Recommendation
    from app.models.skill import Skill


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    education_level: Mapped[str | None] = mapped_column(String(100))
    degree: Mapped[str | None] = mapped_column(String(255))
    branch: Mapped[str | None] = mapped_column(String(255))
    year_of_study: Mapped[int | None] = mapped_column(Integer)
    location: Mapped[str | None] = mapped_column(String(255))
    career_goal_id: Mapped[int | None] = mapped_column(ForeignKey("career_paths.id"))
    resume_text: Mapped[str | None] = mapped_column(Text)
    resume_file_path: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    career_goal: Mapped[CareerPath | None] = relationship(back_populates="students")
    skills: Mapped[list[StudentSkill]] = relationship(back_populates="student", cascade="all, delete-orphan")
    certificates: Mapped[list[Certificate]] = relationship(back_populates="student", cascade="all, delete-orphan")
    recommendations: Mapped[list[Recommendation]] = relationship(back_populates="student")
    preparation_plans: Mapped[list[PreparationPlan]] = relationship(back_populates="student")


class StudentSkill(Base):
    __tablename__ = "student_skills"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), nullable=False)
    proficiency: Mapped[ProficiencyLevel | None] = mapped_column(Enum(ProficiencyLevel, name="proficiency_level"))
    source: Mapped[SkillSource] = mapped_column(Enum(SkillSource, name="skill_source"), default=SkillSource.manual, nullable=False)

    student: Mapped[Student] = relationship(back_populates="skills")
    skill: Mapped[Skill] = relationship(back_populates="student_skills")


class Certificate(Base):
    __tablename__ = "certificates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    issuing_organization: Mapped[str | None] = mapped_column(String(255))
    issue_date: Mapped[date | None] = mapped_column(Date)
    credential_url: Mapped[str | None] = mapped_column(String(500))
    extracted_from_resume: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    student: Mapped[Student] = relationship(back_populates="certificates")
