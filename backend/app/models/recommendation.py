from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import RecommendationStatus

if TYPE_CHECKING:
    from app.models.feedback import Feedback
    from app.models.internship import Internship
    from app.models.student import Student


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    internship_id: Mapped[int] = mapped_column(ForeignKey("internships.id"), nullable=False)
    match_score: Mapped[float] = mapped_column(Float, nullable=False)
    readiness_score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[RecommendationStatus] = mapped_column(Enum(RecommendationStatus, name="recommendation_status"), nullable=False)
    score_breakdown: Mapped[dict | None] = mapped_column(JSON)
    explanation_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    student: Mapped[Student] = relationship(back_populates="recommendations")
    internship: Mapped[Internship] = relationship(back_populates="recommendations")
    feedback: Mapped[list[Feedback]] = relationship(back_populates="recommendation", cascade="all, delete-orphan")
