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
    SEMANTIC_MATCH_CREDIT,
    SEMANTIC_MATCH_THRESHOLD,
    SKILL_MATCH_WEIGHT,
    FEEDBACK_TOO_DIFFICULT_PENALTY,
)
from app.recommendation.semantic import (
    InternshipEmbeddingIndex,
    cosine_similarity,
    embed_text,
    prepare_internship_embedding_index,
)
from app.recommendation.readiness import calculate_readiness
from app.recommendation.personalization import PersonalizationPolicy


@dataclass
class Profile:
    skills: list[str]
    year_of_study: int | None = None
    location: str | None = None
    interests: list[str] | None = None
    preferences: dict[str, Any] | None = None
    career_goal_id: int | None = None
    skill_embeddings: dict[str, list[float]] | None = None
    certificates: list[str] | None = None


def profile_from_student(student: Student) -> Profile:
    return Profile(
        skills=[skill.skill.name for skill in student.skills],
        year_of_study=student.year_of_study,
        location=student.location,
        interests=student.interests or [],
        preferences=student.preferences or {},
        career_goal_id=student.career_goal_id,
        skill_embeddings={_norm(skill.skill.name): skill.skill.embedding for skill in student.skills if skill.skill.embedding},
        certificates=[certificate.name for certificate in student.certificates],
    )


def _norm(value: Any) -> str:
    return str(value).strip().casefold()


def _student_skill_names(profile: Profile) -> set[str]:
    return {_norm(supplied) for supplied in profile.skills}


def _skill_keys(skill) -> set[str]:
    return {_norm(skill.name), *(_norm(alias) for alias in (skill.aliases or []))}


def _skill_match_detail(profile: Profile, internship: Internship) -> tuple[float, dict[str, list]]:
    student_names = _student_skill_names(profile)
    embeddings = profile.skill_embeddings or {}
    required = [link for link in internship.skills if link.requirement_level == RequirementLevel.required]
    preferred = [link for link in internship.skills if link.requirement_level == RequirementLevel.preferred]
    matched_skills: list[dict[str, str]] = []
    missing_critical_skills: list[str] = []
    missing_important_skills: list[str] = []

    def credit(link) -> float:
        if student_names & _skill_keys(link.skill):
            matched_skills.append({"skill_name": link.skill.name, "match_type": "exact"})
            return 1.0
        if not link.skill.embedding:
            (missing_critical_skills if link.requirement_level == RequirementLevel.required else missing_important_skills).append(link.skill.name)
            return 0.0
        for skill_name in student_names:
            if skill_name not in embeddings:
                embeddings[skill_name] = embed_text(skill_name)
        highest = max((cosine_similarity(embeddings[name], link.skill.embedding) for name in student_names), default=0.0)
        if highest >= SEMANTIC_MATCH_THRESHOLD:
            matched_skills.append({"skill_name": link.skill.name, "match_type": "semantic"})
            return SEMANTIC_MATCH_CREDIT
        (missing_critical_skills if link.requirement_level == RequirementLevel.required else missing_important_skills).append(link.skill.name)
        return 0.0

    # Preserve the exact single-pass per-skill credits for Phase 6 readiness.
    required_skill_credits = [credit(link) for link in required]
    preferred_skill_credits = [credit(link) for link in preferred]
    matched_required = sum(required_skill_credits)
    matched_preferred = sum(preferred_skill_credits)
    required_ratio = matched_required / len(required) if required else 0.0
    preferred_ratio = matched_preferred / len(preferred) if preferred else 0.0
    # Required skills carry 70% of this component and preferred skills 30%.
    if required and preferred:
        score = (required_ratio * 0.7 + preferred_ratio * 0.3) * 100
    elif required:
        score = required_ratio * 100
    else:
        score = preferred_ratio * 100
    return score, {
        "matched_skills": matched_skills,
        "missing_critical_skills": missing_critical_skills,
        "missing_important_skills": missing_important_skills,
        "required_skill_credits": required_skill_credits,
    }


def _skill_match(profile: Profile, internship: Internship) -> float:
    return _skill_match_detail(profile, internship)[0]


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


def _interest_match(profile: Profile, internship: Internship, embedding_index: InternshipEmbeddingIndex | None = None, precomputed: dict[int, float] | None = None) -> float:
    interests = profile.interests or []
    if not interests:
        return 0.0
    if precomputed is not None:
        return precomputed.get(internship.id, 0.0)
    matched = 0
    if internship.description_embedding:
        for interest in interests:
            interest_embedding = embed_text(interest)
            if embedding_index is None:
                similarity = cosine_similarity(interest_embedding, internship.description_embedding)
            else:
                similarity = embedding_index.similarity(internship.id, interest_embedding)
            matched += similarity >= SEMANTIC_MATCH_THRESHOLD
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
        scores.append(100.0 if _norm(preferences["work_mode"]) == _norm(internship.work_mode.value if internship.work_mode else "") else 0.0)
    if preferences.get("duration"):
        scores.append(100.0 if _norm(preferences["duration"]) == _norm(internship.duration) else 0.0)
    return sum(scores) / len(scores) if scores else 0.0


def _status(score: float, readiness_score: float) -> RecommendationStatus:
    if readiness_score >= APPLY_NOW_THRESHOLD and score >= APPLY_NOW_THRESHOLD:
        return RecommendationStatus.apply_now
    if readiness_score >= APPLY_UPSKILL_THRESHOLD:
        return RecommendationStatus.apply_upskill
    return RecommendationStatus.prepare_first


def score_internship(profile: Profile, internship: Internship, embedding_index: InternshipEmbeddingIndex | None = None, interest_scores: dict[int, float] | None = None) -> dict[str, Any]:
    skill_score, skill_detail = _skill_match_detail(profile, internship)
    raw = {
        "skill_match": skill_score,
        "career_alignment": _career_alignment(profile, internship),
        "interest_match": _interest_match(profile, internship, embedding_index, interest_scores),
        "location_match": _location_match(profile, internship),
        "education_eligibility": _education_score(profile, internship),
        "preference_match": _preference_match(profile, internship),
    }
    readiness_score, readiness_components = calculate_readiness(profile, internship, skill_detail)
    raw["readiness"] = readiness_score
    weights = {
        "skill_match": SKILL_MATCH_WEIGHT, "career_alignment": CAREER_ALIGNMENT_WEIGHT,
        "interest_match": INTEREST_MATCH_WEIGHT, "location_match": LOCATION_MATCH_WEIGHT,
        "education_eligibility": EDUCATION_ELIGIBILITY_WEIGHT, "preference_match": PREFERENCE_MATCH_WEIGHT,
        "readiness": READINESS_WEIGHT,
    }
    breakdown = {name: {"raw": value, "weighted": value * weights[name]} for name, value in raw.items()}
    final_score = min(100.0, max(0.0, sum(item["weighted"] for item in breakdown.values())))
    return {
        "match_score": round(final_score, 2), "readiness_score": round(readiness_score, 2),
        "status": _status(final_score, readiness_score), "score_breakdown": breakdown,
        "_readiness_components": readiness_components,
        "_skill_detail": skill_detail,
    }


def recommend(
    profile: Profile,
    internships: list[Internship],
    limit: int = 5,
    personalization: PersonalizationPolicy | None = None,
) -> list[dict[str, Any]]:
    candidates = internships
    if personalization is not None:
        candidates = [
            item for item in internships
            if item.id not in personalization.excluded_internship_ids
            and item.sector not in personalization.excluded_sectors
            and item.location not in personalization.excluded_locations
        ]
    eligible = [item for item in candidates if profile.year_of_study is None or item.min_year is None or item.min_year <= profile.year_of_study]
    embedding_index = prepare_internship_embedding_index(internships)
    interest_scores: dict[int, float] = {}
    if profile.interests:
        match_counts = sum(
            embedding_index.similarities(embed_text(interest)) >= SEMANTIC_MATCH_THRESHOLD
            for interest in profile.interests
        )
        interest_scores = {
            internship.id: float(match_counts[index] / len(profile.interests) * 100)
            for index, internship in enumerate(internships)
        }
    results = []
    for internship in eligible:
        scored = score_internship(profile, internship, embedding_index, interest_scores)
        adjustments: list[dict[str, Any]] = []
        if personalization is not None:
            sector_penalty = personalization.penalized_sectors.get(internship.sector or "", 0)
            if sector_penalty:
                scored["match_score"] = round(max(0.0, scored["match_score"] - sector_penalty), 2)
                adjustments.append({"type": "sector_penalty", "reason": "not_interested", "points": -sector_penalty})
            if personalization.too_difficult_flag and scored["readiness_score"] < 60:
                scored["match_score"] = round(max(0.0, scored["match_score"] - FEEDBACK_TOO_DIFFICULT_PENALTY), 2)
                adjustments.append({"type": "readiness_penalty", "reason": "too_difficult", "points": -FEEDBACK_TOO_DIFFICULT_PENALTY})
            scored["status"] = _status(scored["match_score"], scored["readiness_score"])
        scored["personalization_adjustments"] = adjustments
        results.append({"internship": internship, **scored})
    results.sort(key=lambda result: (-result["match_score"], result["internship"].id))
    return results[:limit]
