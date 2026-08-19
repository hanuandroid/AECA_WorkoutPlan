"""Typed data models shared across the workout plan generator pipeline."""

from dataclasses import dataclass, field

# Allowed dropdown values. Kept as tuples (not a free-form Enum) so validator.py
# and app.py can both use them directly as Streamlit `options=` lists.
FITNESS_GOALS: tuple[str, ...] = (
    "Build muscle",
    "Lose fat",
    "General fitness",
    "Improve endurance",
)

EXPERIENCE_LEVELS: tuple[str, ...] = (
    "Beginner",
    "Intermediate",
    "Advanced",
)

EQUIPMENT_OPTIONS: tuple[str, ...] = (
    "No equipment",
    "Home dumbbells",
    "Full gym",
)

MIN_DAYS_PER_WEEK: int = 1
MAX_DAYS_PER_WEEK: int = 7


@dataclass(frozen=True)
class WorkoutRequest:
    """Structured user input collected by the Streamlit UI."""

    fitness_goal: str
    experience_level: str
    days_per_week: int
    equipment: str
    limitations: str = ""

    @property
    def has_limitations(self) -> bool:
        return bool(self.limitations.strip())


@dataclass(frozen=True)
class ValidationResult:
    """Result of validating a WorkoutRequest before it enters the pipeline."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ServiceResult:
    """Result of the end-to-end workout generation pipeline."""

    success: bool
    plan_text: str = ""
    error_message: str = ""
