from enum import Enum


class ProficiencyLevel(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class SkillSource(str, Enum):
    manual = "manual"
    resume_extracted = "resume_extracted"


class WorkMode(str, Enum):
    remote = "remote"
    hybrid = "hybrid"
    onsite = "onsite"


class RequirementLevel(str, Enum):
    required = "required"
    preferred = "preferred"


class RecommendationStatus(str, Enum):
    apply_now = "apply_now"
    apply_upskill = "apply_upskill"
    prepare_first = "prepare_first"


class FeedbackReason(str, Enum):
    wrong_skills = "wrong_skills"
    wrong_location = "wrong_location"
    wrong_sector = "wrong_sector"
    not_interested = "not_interested"
    too_difficult = "too_difficult"
    already_applied = "already_applied"


class PlanPriority(str, Enum):
    critical = "critical"
    important = "important"
    optional = "optional"
