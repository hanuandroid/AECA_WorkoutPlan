from unittest.mock import patch

from src.groq_client import GroqClientError
from src.models import WorkoutRequest
from src.workout_service import EMPTY_RESPONSE_MESSAGE, generate_workout_plan


def _request(**overrides: object) -> WorkoutRequest:
    defaults: dict[str, object] = {
        "fitness_goal": "Build muscle",
        "experience_level": "Beginner",
        "days_per_week": 3,
        "equipment": "Home dumbbells",
        "limitations": "",
    }
    defaults.update(overrides)
    return WorkoutRequest(**defaults)  # type: ignore[arg-type]


@patch("src.workout_service.call_groq")
def test_invalid_input_never_calls_groq(mock_call_groq) -> None:
    result = generate_workout_plan(_request(days_per_week=0))

    assert not result.success
    assert result.error_message
    mock_call_groq.assert_not_called()


@patch("src.workout_service.call_groq")
def test_valid_input_returns_successful_plan(mock_call_groq) -> None:
    mock_call_groq.return_value = "# Weekly Workout Plan\n\n## Day 1 - Full Body"

    result = generate_workout_plan(_request())

    assert result.success
    assert "Day 1" in result.plan_text
    mock_call_groq.assert_called_once()


@patch("src.workout_service.call_groq")
def test_groq_failure_surfaces_friendly_error(mock_call_groq) -> None:
    mock_call_groq.side_effect = GroqClientError("The AI service is unavailable.")

    result = generate_workout_plan(_request())

    assert not result.success
    assert result.error_message == "The AI service is unavailable."


@patch("src.workout_service.call_groq")
def test_empty_response_surfaces_fallback_message(mock_call_groq) -> None:
    mock_call_groq.return_value = ""

    result = generate_workout_plan(_request())

    assert not result.success
    assert result.error_message == EMPTY_RESPONSE_MESSAGE


@patch("src.workout_service.call_groq")
def test_malformed_response_surfaces_fallback_message(mock_call_groq) -> None:
    mock_call_groq.return_value = "Sure! Here's some unrelated chat text."

    result = generate_workout_plan(_request())

    assert not result.success
    assert result.error_message == EMPTY_RESPONSE_MESSAGE


@patch("src.workout_service.call_groq")
def test_unexpected_exception_does_not_escape(mock_call_groq) -> None:
    mock_call_groq.side_effect = RuntimeError("boom")

    result = generate_workout_plan(_request())

    assert not result.success
    assert result.error_message
