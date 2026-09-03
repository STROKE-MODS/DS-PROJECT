from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import RequirementLevel, WorkMode

if TYPE_CHECKING:
    from app.models.career_path import CareerPath
    from app.models.recommendation import Recommendation
    from app.models.skill import Skill


class Internship(Base):
    __tablename__ = "internships"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    sector: Mapped[str | None] = mapped_column(String(255))
    education_required: Mapped[str | None] = mapped_column(String(255))
    min_year: Mapped[int | None] = mapped_column(Integer)
    location: Mapped[str | None] = mapped_column(String(255))
    work_mode: Mapped[WorkMode | None] = mapped_column(Enum(WorkMode, name="work_mode"))
    duration: Mapped[str | None] = mapped_column(String(100))
    stipend: Mapped[str | None] = mapped_column(String(100))
    experience_required: Mapped[str | None] = mapped_column(String(255))
    career_path_id: Mapped[int | None] = mapped_column(ForeignKey("career_paths.id"))
    is_demo_data: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    career_path: Mapped[CareerPath | None] = relationship(back_populates="internships")
    skills: Mapped[list[InternshipSkill]] = relationship(back_populates="internship", cascade="all, delete-orphan")
    recommendations: Mapped[list[Recommendation]] = relationship(back_populates="internship")
    preparation_plans: Mapped[list[PreparationPlan]] = relationship(back_populates="internship")


class InternshipSkill(Base):
    __tablename__ = "internship_skills"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    internship_id: Mapped[int] = mapped_column(ForeignKey("internships.id"), nullable=False)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), nullable=False)
    requirement_level: Mapped[RequirementLevel] = mapped_column(Enum(RequirementLevel, name="requirement_level"), nullable=False)

    internship: Mapped[Internship] = relationship(back_populates="skills")
    skill: Mapped[Skill] = relationship(back_populates="internship_skills")
