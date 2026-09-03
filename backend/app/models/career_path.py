from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.internship import Internship
    from app.models.student import Student


class CareerPath(Base):
    __tablename__ = "career_paths"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    next_step_id: Mapped[int | None] = mapped_column(ForeignKey("career_paths.id"))

    next_step: Mapped[CareerPath | None] = relationship(
        "CareerPath", remote_side=[id], back_populates="previous_steps"
    )
    previous_steps: Mapped[list[CareerPath]] = relationship(
        "CareerPath", back_populates="next_step"
    )
    students: Mapped[list[Student]] = relationship(back_populates="career_goal")
    internships: Mapped[list[Internship]] = relationship(back_populates="career_path")
