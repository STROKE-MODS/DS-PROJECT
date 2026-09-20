from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.models import Internship, RecommendationStatus, Student
from app.models.enums import RequirementLevel
from app.recommendation.config import (
    APPLY_NOW_THRESHOLD,
    APPLY_UPSKILL_THRESHOLD,
    CAREER_ALIGNMENT_WEIGHT,
    EDUCATION_ELIGIBILITY_WEIGHT,
    INTEREST_MATCH_WEIGHT,
    LOCATION_MATCH_WEIGHT,
    PREFERENCE_MATCH_WEIGHT,
    READINESS_WEIGHT,
    SKILL_MATCH_WEIGHT,
)


@dataclass
class Profile:
    skills: list[str]
    year_of_study: int | None = None
    location: str | None = None
    interests: list[str] | None = None
    preferences: dict[str, Any] | None = None
    career_goal_id: int | None = None


def profile_from_student(student: Student) -> Profile:
    return Profile(
        skills=[skill.skill.name for skill in student.skills],
        year_of_study=student.year_of_study,
        location=student.location,
        interests=student.interests or [],
        preferences=student.preferences or {},
        career_goal_id=student.career_goal_id,
    )


def _norm(value: Any) -> str:
    return str(value).strip().casefold()


def _student_skill_names(profile: Profile, internship: Internship) -> set[str]:
    names: set[str] = set()
    for supplied in profile.skills:
        names.add(_norm(supplied))
    return names


def _skill_keys(skill) -> set[str]:
    return {_norm(skill.name), *(_norm(alias) for alias in (skill.aliases or []))}


def _skill_match(profile: Profile, internship: Internship) -> float:
    student_names = _student_skill_names(profile, internship)
    required = [link for link in internship.skills if link.requirement_level == RequirementLevel.required]
    preferred = [link for link in internship.skills if link.requirement_level == RequirementLevel.preferred]
    matched_required = sum(bool(student_names & _skill_keys(link.skill)) for link in required)
    matched_preferred = sum(bool(student_names & _skill_keys(link.skill)) for link in preferred)
    required_ratio = matched_required / len(required) if required else 0.0
    preferred_ratio = matched_preferred / len(preferred) if preferred else 0.0
    # Required skills carry 70% of this component and preferred skills 30%.
    if required and preferred:
        return (required_ratio * 0.7 + preferred_ratio * 0.3) * 100
    if required:
        return required_ratio * 100
    return preferred_ratio * 100


def _career_alignment(profile: Profile, internship: Internship) -> float:
    if profile.career_goal_id is None or internship.career_path_id is None:
        return 0.0
    if internship.career_path_id == profile.career_goal_id:
        return 100.0
    path = internship.career_path
    if path and path.next_step_id == profile.career_goal_id:
        return 70.0
    # The reverse one-hop direction: the internship is the goal's next step.
    if profile.career_goal_id == getattr(path, "next_step_id", None):
        return 70.0
    if path and any(previous.id == profile.career_goal_id for previous in path.previous_steps):
        return 70.0
    return 0.0


def _interest_match(profile: Profile, internship: Internship) -> float:
    interests = profile.interests or []
    if not interests:
        return 0.0
    text = _norm(f"{internship.sector or ''} {internship.description or ''}")
    matched = sum(_norm(interest) in text for interest in interests)
    return matched / len(interests) * 100


def _location_match(profile: Profile, internship: Internship) -> float:
    preference_location = (profile.preferences or {}).get("location") or profile.location
    if not preference_location:
        return 0.0
    if _norm(internship.location) == "remote" or _norm(internship.work_mode) == "remote":
        return 100.0
    return 100.0 if _norm(preference_location) == _norm(internship.location) else 0.0


def _education_score(profile: Profile, internship: Internship) -> float:
    if profile.year_of_study is None or internship.min_year is None:
        return 50.0
    if profile.year_of_study == internship.min_year:
        return 80.0
    if profile.year_of_study >= internship.min_year + 1:
        return 100.0
    return 0.0


def _preference_match(profile: Profile, internship: Internship) -> float:
    preferences = profile.preferences or {}
    scores: list[float] = []
    if preferences.get("work_mode"):
        scores.append(100.0 if _norm(preferences["work_mode"]) == _norm(internship.work_mode) else 0.0)
    if preferences.get("duration"):
        scores.append(100.0 if _norm(preferences["duration"]) == _norm(internship.duration) else 0.0)
    return sum(scores) / len(scores) if scores else 0.0


def _status(score: float) -> RecommendationStatus:
    # TODO(Phase 6): Separate match-score status from real readiness status.
    if score >= APPLY_NOW_THRESHOLD:
        return RecommendationStatus.apply_now
    if score >= APPLY_UPSKILL_THRESHOLD:
        return RecommendationStatus.apply_upskill
    return RecommendationStatus.prepare_first


def score_internship(profile: Profile, internship: Internship) -> dict[str, Any]:
    raw = {
        "skill_match": _skill_match(profile, internship),
        "career_alignment": _career_alignment(profile, internship),
        "interest_match": _interest_match(profile, internship),
        "location_match": _location_match(profile, internship),
        "education_eligibility": _education_score(profile, internship),
        "preference_match": _preference_match(profile, internship),
    }
    # TODO(Phase 6): Replace with real readiness engine per spec Section 10.
    raw["readiness"] = 70.0
    weights = {
        "skill_match": SKILL_MATCH_WEIGHT, "career_alignment": CAREER_ALIGNMENT_WEIGHT,
        "interest_match": INTEREST_MATCH_WEIGHT, "location_match": LOCATION_MATCH_WEIGHT,
        "education_eligibility": EDUCATION_ELIGIBILITY_WEIGHT, "preference_match": PREFERENCE_MATCH_WEIGHT,
        "readiness": READINESS_WEIGHT,
    }
    breakdown = {name: {"raw": value, "weighted": value * weights[name]} for name, value in raw.items()}
    final_score = min(100.0, max(0.0, sum(item["weighted"] for item in breakdown.values())))
    return {"match_score": round(final_score, 2), "readiness_score": 70.0, "status": _status(final_score), "score_breakdown": breakdown}


def recommend(profile: Profile, internships: list[Internship], limit: int = 5) -> list[dict[str, Any]]:
    eligible = [item for item in internships if profile.year_of_study is None or item.min_year is None or item.min_year <= profile.year_of_study]
    results = []
    for internship in eligible:
        scored = score_internship(profile, internship)
        results.append({"internship": internship, **scored})
    results.sort(key=lambda result: (-result["match_score"], result["internship"].id))
    return results[:limit]
