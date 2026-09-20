from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.internship import InternshipSkill
    from app.models.student import StudentSkill
    from app.models.preparation_plan import PreparationPlan


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    aliases: Mapped[list[str] | None] = mapped_column(JSON)
    embedding: Mapped[list[float] | None] = mapped_column(JSON)

    student_skills: Mapped[list[StudentSkill]] = relationship(back_populates="skill")
    internship_skills: Mapped[list[InternshipSkill]] = relationship(back_populates="skill")
    preparation_plans: Mapped[list[PreparationPlan]] = relationship(back_populates="missing_skill")
