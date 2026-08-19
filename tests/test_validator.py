from src.models import WorkoutRequest
from src.validator import validate_workout_request


def _valid_request(**overrides: object) -> WorkoutRequest:
    defaults: dict[str, object] = {
        "fitness_goal": "Build muscle",
        "experience_level": "Beginner",
        "days_per_week": 3,
        "equipment": "Home dumbbells",
        "limitations": "",
    }
    defaults.update(overrides)
    return WorkoutRequest(**defaults)  # type: ignore[arg-type]


def test_valid_request_passes() -> None:
    result = validate_workout_request(_valid_request())
    assert result.is_valid
    assert result.errors == []


def test_one_day_is_valid_boundary() -> None:
    result = validate_workout_request(_valid_request(days_per_week=1))
    assert result.is_valid


def test_seven_days_is_valid_boundary() -> None:
    result = validate_workout_request(_valid_request(days_per_week=7))
    assert result.is_valid


def test_zero_days_is_invalid() -> None:
    result = validate_workout_request(_valid_request(days_per_week=0))
    assert not result.is_valid
    assert result.errors


def test_eight_days_is_invalid() -> None:
    result = validate_workout_request(_valid_request(days_per_week=8))
    assert not result.is_valid
    assert result.errors


def test_negative_days_is_invalid() -> None:
    result = validate_workout_request(_valid_request(days_per_week=-1))
    assert not result.is_valid


def test_missing_goal_is_invalid() -> None:
    result = validate_workout_request(_valid_request(fitness_goal=""))
    assert not result.is_valid
    assert any("goal" in error.lower() for error in result.errors)


def test_invalid_goal_value_is_rejected() -> None:
    result = validate_workout_request(_valid_request(fitness_goal="Get ripped fast"))
    assert not result.is_valid


def test_missing_experience_is_invalid() -> None:
    result = validate_workout_request(_valid_request(experience_level=""))
    assert not result.is_valid
    assert any("experience" in error.lower() for error in result.errors)


def test_missing_equipment_is_invalid() -> None:
    result = validate_workout_request(_valid_request(equipment=""))
    assert not result.is_valid
    assert any("equipment" in error.lower() for error in result.errors)


def test_multiple_errors_are_all_reported() -> None:
    result = validate_workout_request(
        _valid_request(fitness_goal="", experience_level="", days_per_week=0)
    )
    assert not result.is_valid
    assert len(result.errors) >= 3


def test_limitations_optional_and_valid_when_empty() -> None:
    result = validate_workout_request(_valid_request(limitations=""))
    assert result.is_valid


def test_limitations_optional_and_valid_when_present() -> None:
    result = validate_workout_request(_valid_request(limitations="bad knees"))
    assert result.is_valid
