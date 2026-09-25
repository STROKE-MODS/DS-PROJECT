from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Feedback, Internship, Recommendation
from app.models.enums import FeedbackReason
from app.recommendation.config import (
    FEEDBACK_ALREADY_APPLIED_THRESHOLD,
    FEEDBACK_LOCATION_EXCLUSION_THRESHOLD,
    FEEDBACK_NOT_INTERESTED_PENALTY,
    FEEDBACK_NOT_INTERESTED_THRESHOLD,
    FEEDBACK_SECTOR_EXCLUSION_THRESHOLD,
    FEEDBACK_TOO_DIFFICULT_PENALTY,
    FEEDBACK_TOO_DIFFICULT_THRESHOLD,
)


@dataclass(frozen=True)
class PersonalizationPolicy:
    excluded_internship_ids: set[int] = field(default_factory=set)
    excluded_sectors: set[str] = field(default_factory=set)
    excluded_locations: set[str] = field(default_factory=set)
    penalized_sectors: dict[str, int] = field(default_factory=dict)
    too_difficult_flag: bool = False


def build_personalization_policy(student_id: int, db: Session) -> PersonalizationPolicy:
    """Aggregate one student's feedback in one joined query; ad-hoc profiles never call this."""
    rows = db.execute(
        select(
            Feedback.reason,
            Recommendation.internship_id,
            Internship.sector,
            Internship.location,
        )
        .join(Recommendation, Feedback.recommendation_id == Recommendation.id)
        .join(Internship, Recommendation.internship_id == Internship.id)
        .where(Recommendation.student_id == student_id, Feedback.is_useful.is_(False))
    ).all()

    already_applied: set[int] = set()
    sector_counts: Counter[str] = Counter()
    location_counts: Counter[str] = Counter()
    not_interested_counts: Counter[str] = Counter()
    too_difficult_count = 0

    for reason, internship_id, sector, location in rows:
        if reason == FeedbackReason.already_applied:
            already_applied.add(internship_id)
        elif reason == FeedbackReason.wrong_sector and sector:
            sector_counts[sector] += 1
        elif reason == FeedbackReason.wrong_location and location:
            location_counts[location] += 1
        elif reason == FeedbackReason.not_interested and sector:
            not_interested_counts[sector] += 1
        elif reason == FeedbackReason.too_difficult:
            too_difficult_count += 1
        # wrong_skills is intentionally stored for analysis only. The existing
        # skill_match component already captures skill fit, so no second signal is applied.

    excluded_internship_ids = already_applied if FEEDBACK_ALREADY_APPLIED_THRESHOLD <= 1 else set()
    excluded_sectors = {
        sector for sector, count in sector_counts.items()
        if count >= FEEDBACK_SECTOR_EXCLUSION_THRESHOLD
    }
    excluded_locations = {
        location for location, count in location_counts.items()
        if count >= FEEDBACK_LOCATION_EXCLUSION_THRESHOLD
    }
    penalized_sectors = {
        sector: FEEDBACK_NOT_INTERESTED_PENALTY
        for sector, count in not_interested_counts.items()
        if count >= FEEDBACK_NOT_INTERESTED_THRESHOLD
    }
    return PersonalizationPolicy(
        excluded_internship_ids=excluded_internship_ids,
        excluded_sectors=excluded_sectors,
        excluded_locations=excluded_locations,
        penalized_sectors=penalized_sectors,
        too_difficult_flag=too_difficult_count >= FEEDBACK_TOO_DIFFICULT_THRESHOLD,
    )


__all__ = ["PersonalizationPolicy", "build_personalization_policy"]
