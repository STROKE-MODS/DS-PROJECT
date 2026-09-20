from __future__ import annotations

from typing import Any

from app.recommendation.config import (
    READINESS_CERTIFICATE_WEIGHT,
    READINESS_SENIORITY_WEIGHT,
    READINESS_SKILL_WEIGHT,
)


def skill_depth(skill_detail: dict[str, Any], required_count: int) -> float:
    """Use the exact/semantic credits already computed by Phase 5 skill matching."""
    if required_count == 0:
        return 100.0
    credits = skill_detail.get("required_skill_credits", [])
    return sum(credits) / required_count * 100.0


def certificate_signal(profile: Any, internship: Any) -> float:
    """Ad-hoc profiles have no certificates table access, so their signal is 0."""
    certificates = getattr(profile, "certificates", None) or []
    if not certificates:
        return 0.0
    targets = [internship.sector or ""]
    targets.extend(link.skill.name for link in internship.skills)
    targets.extend(alias for link in internship.skills for alias in (link.skill.aliases or []))
    normalized_certificates = [str(name).casefold().strip() for name in certificates]
    normalized_targets = [str(target).casefold().strip() for target in targets if target]
    for certificate_name in normalized_certificates:
        if any(certificate_name in target or target in certificate_name for target in normalized_targets):
            return 100.0
    return 0.0


def seniority_score(year_of_study: int | None, min_year: int | None) -> float:
    if year_of_study is None or min_year is None:
        return 50.0
    if year_of_study < min_year:
        return 0.0
    if year_of_study == min_year:
        return 50.0
    if year_of_study == min_year + 1:
        return 75.0
    return 100.0


def calculate_readiness(profile: Any, internship: Any, skill_detail: dict[str, Any]) -> tuple[float, dict[str, float]]:
    required_count = sum(
        1 for link in internship.skills if getattr(link.requirement_level, "value", link.requirement_level) == "required"
    )
    components = {
        "skill_depth": skill_depth(skill_detail, required_count),
        "certificate_signal": certificate_signal(profile, internship),
        "seniority_score": seniority_score(profile.year_of_study, internship.min_year),
    }
    readiness = (
        components["skill_depth"] * READINESS_SKILL_WEIGHT
        + components["certificate_signal"] * READINESS_CERTIFICATE_WEIGHT
        + components["seniority_score"] * READINESS_SENIORITY_WEIGHT
    )
    return readiness, components
