from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Feedback, FeedbackReason, Recommendation

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/feedback", tags=["feedback"])


class FeedbackRequest(BaseModel):
    recommendation_id: int
    is_useful: bool
    reason: FeedbackReason | None = None


@router.post("")
def create_feedback(payload: FeedbackRequest, db: Session = Depends(get_db)) -> dict:
    recommendation = db.scalar(
        select(Recommendation).where(Recommendation.id == payload.recommendation_id)
    )
    if recommendation is None:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    existing = db.scalar(
        select(Feedback).where(Feedback.recommendation_id == payload.recommendation_id)
    )
    if existing is not None:
        # Reject duplicates rather than silently replacing the student's prior signal.
        raise HTTPException(
            status_code=409,
            detail="Feedback already exists for this recommendation",
        )

    if not payload.is_useful and payload.reason is None:
        logger.info(
            "Negative feedback submitted without a reason: recommendation_id=%s",
            payload.recommendation_id,
        )
    reason = None if payload.is_useful else payload.reason
    feedback = Feedback(
        recommendation_id=payload.recommendation_id,
        is_useful=payload.is_useful,
        reason=reason,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return {
        "id": feedback.id,
        "recommendation_id": feedback.recommendation_id,
        "is_useful": feedback.is_useful,
        "reason": feedback.reason.value if feedback.reason else None,
        "created_at": feedback.created_at,
    }


__all__ = ["router"]
