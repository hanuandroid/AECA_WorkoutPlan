"""Validation for structured workout requests.

Never raises — always returns a ValidationResult so invalid input can be shown
as a friendly Streamlit message instead of crashing the app.
"""

from src.models import (
    EQUIPMENT_OPTIONS,
    EXPERIENCE_LEVELS,
    FITNESS_GOALS,
    MAX_DAYS_PER_WEEK,
    MIN_DAYS_PER_WEEK,
    ValidationResult,
    WorkoutRequest,
)

ERROR_MISSING_GOAL = "Please select a fitness goal."
ERROR_INVALID_GOAL = "Please select a valid fitness goal from the list."
ERROR_MISSING_EXPERIENCE = "Please select your experience level."
ERROR_INVALID_EXPERIENCE = "Please select a valid experience level from the list."
ERROR_MISSING_EQUIPMENT = "Please select your available equipment."
ERROR_INVALID_EQUIPMENT = "Please select a valid equipment option from the list."
ERROR_INVALID_DAYS = (
    f"Please choose a number of training days between "
    f"{MIN_DAYS_PER_WEEK} and {MAX_DAYS_PER_WEEK}."
)


def validate_workout_request(request: WorkoutRequest) -> ValidationResult:
    """Validate a WorkoutRequest, collecting every error rather than failing fast."""
    errors: list[str] = []

    if not request.fitness_goal.strip():
        errors.append(ERROR_MISSING_GOAL)
    elif request.fitness_goal not in FITNESS_GOALS:
        errors.append(ERROR_INVALID_GOAL)

    if not request.experience_level.strip():
        errors.append(ERROR_MISSING_EXPERIENCE)
    elif request.experience_level not in EXPERIENCE_LEVELS:
        errors.append(ERROR_INVALID_EXPERIENCE)

    if not request.equipment.strip():
        errors.append(ERROR_MISSING_EQUIPMENT)
    elif request.equipment not in EQUIPMENT_OPTIONS:
        errors.append(ERROR_INVALID_EQUIPMENT)

    if not _is_valid_day_count(request.days_per_week):
        errors.append(ERROR_INVALID_DAYS)

    return ValidationResult(is_valid=not errors, errors=errors)


def _is_valid_day_count(days_per_week: int) -> bool:
    if isinstance(days_per_week, bool) or not isinstance(days_per_week, int):
        return False
    return MIN_DAYS_PER_WEEK <= days_per_week <= MAX_DAYS_PER_WEEK
