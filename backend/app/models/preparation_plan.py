from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import PlanPriority

if TYPE_CHECKING:
    from app.models.internship import Internship
    from app.models.skill import Skill
    from app.models.student import Student


class PreparationPlan(Base):
    __tablename__ = "preparation_plans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    internship_id: Mapped[int] = mapped_column(ForeignKey("internships.id"), nullable=False)
    missing_skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), nullable=False)
    plan_steps: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    priority: Mapped[PlanPriority] = mapped_column(Enum(PlanPriority, name="plan_priority"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    student: Mapped[Student] = relationship(back_populates="preparation_plans")
    internship: Mapped[Internship] = relationship(back_populates="preparation_plans")
    missing_skill: Mapped[Skill] = relationship(back_populates="preparation_plans")
