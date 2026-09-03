from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import FeedbackReason

if TYPE_CHECKING:
    from app.models.recommendation import Recommendation


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    recommendation_id: Mapped[int] = mapped_column(ForeignKey("recommendations.id"), nullable=False)
    is_useful: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reason: Mapped[FeedbackReason | None] = mapped_column(Enum(FeedbackReason, name="feedback_reason"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    recommendation: Mapped[Recommendation] = relationship(back_populates="feedback")
