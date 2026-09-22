from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Internship, PreparationPlan, Skill
from app.models.enums import PlanPriority
from app.recommendation.config import SEMANTIC_MATCH_THRESHOLD
from app.recommendation.engine import Profile, _norm
from app.recommendation.semantic import cosine_similarity, embed_text


def _skill_keys(skill: Skill) -> set[str]:
    return {_norm(skill.name), *(_norm(alias) for alias in (skill.aliases or []))}


def _profile_has_skill(profile: Profile, skill: Skill) -> bool:
    student_names = {_norm(name) for name in profile.skills}
    if student_names & _skill_keys(skill):
        return True

    if not skill.embedding or not student_names:
        return False

    embeddings = profile.skill_embeddings or {}
    for name in student_names:
        if name not in embeddings:
            embeddings[name] = embed_text(name)
        if cosine_similarity(embeddings[name], skill.embedding) >= SEMANTIC_MATCH_THRESHOLD:
            return True
    return False


def _adjacent_path_ids(internship: Internship) -> set[int]:
    path = internship.career_path
    if path is None:
        return set()

    adjacent: set[int] = set()
    if path.next_step_id is not None:
        adjacent.add(path.next_step_id)
    adjacent.update(previous.id for previous in (path.previous_steps or []))
    return adjacent


def compute_optional_skills(profile: Profile, internship: Internship, internships: Iterable[Internship]) -> list[str]:
    """Return up to five common skills from one-hop adjacent career paths."""
    adjacent_path_ids = _adjacent_path_ids(internship)
    if not adjacent_path_ids:
        return []

    current_skill_ids = {link.skill_id for link in internship.skills}
    frequencies: Counter[tuple[int, str]] = Counter()
    skill_objects: dict[int, Skill] = {}

    for candidate in internships:
        if candidate.id == internship.id or candidate.career_path_id not in adjacent_path_ids:
            continue
        for link in candidate.skills:
            if link.skill_id in current_skill_ids or _profile_has_skill(profile, link.skill):
                continue
            key = (link.skill_id, link.skill.name)
            frequencies[key] += 1
            skill_objects[link.skill_id] = link.skill

    ranked = sorted(frequencies.items(), key=lambda item: (-item[1], item[0][1].casefold()))
    return [skill_objects[skill_id].name for (skill_id, _), _count in ranked[:5]]


def build_preparation_plan(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Build deterministic four-step plans from the existing Phase 5 skill gaps."""
    detail = result["_skill_detail"]
    entries: list[dict[str, Any]] = []
    for priority, skill_names in (
        (PlanPriority.critical.value, detail["missing_critical_skills"]),
        (PlanPriority.important.value, detail["missing_important_skills"]),
    ):
        for skill_name in skill_names:
            entries.append(
                {
                    "skill_name": skill_name,
                    "priority": priority,
                    "steps": [
                        f"Learn {skill_name} basics",
                        f"Build one small project demonstrating {skill_name}",
                        f"Add the {skill_name} project to your resume or portfolio",
                        f"Apply, highlighting your {skill_name} project",
                    ],
                }
            )
    return entries


def persist_preparation_plans(
    db: Session,
    student_id: int,
    internship_id: int,
    plan_entries: list[dict[str, Any]],
) -> None:
    """Persist plans idempotently for a student/internship recommendation."""
    if not plan_entries:
        return

    names = [entry["skill_name"] for entry in plan_entries]
    skills = db.scalars(select(Skill).where(Skill.name.in_(names))).all()
    skills_by_name = {skill.name: skill for skill in skills}
    skill_ids = [skills_by_name[name].id for name in names if name in skills_by_name]
    existing_ids = set(
        db.scalars(
            select(PreparationPlan.missing_skill_id).where(
                PreparationPlan.student_id == student_id,
                PreparationPlan.internship_id == internship_id,
                PreparationPlan.missing_skill_id.in_(skill_ids),
            )
        ).all()
    ) if skill_ids else set()

    for entry in plan_entries:
        skill = skills_by_name.get(entry["skill_name"])
        if skill is None or skill.id in existing_ids:
            continue
        db.add(
            PreparationPlan(
                student_id=student_id,
                internship_id=internship_id,
                missing_skill_id=skill.id,
                plan_steps=entry["steps"],
                priority=PlanPriority(entry["priority"]),
            )
        )
        existing_ids.add(skill.id)


def enrich_result(
    result: dict[str, Any],
    profile: Profile,
    internships: Iterable[Internship],
    db: Session | None = None,
    student_id: int | None = None,
) -> None:
    internship = result["internship"]
    result["optional_skills"] = compute_optional_skills(profile, internship, internships)
    result["preparation_plan"] = build_preparation_plan(result)
    if db is not None and student_id is not None:
        persist_preparation_plans(db, student_id, internship.id, result["preparation_plan"])


__all__ = [
    "build_preparation_plan",
    "compute_optional_skills",
    "enrich_result",
    "persist_preparation_plans",
]
