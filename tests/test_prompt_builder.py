from src.models import WorkoutRequest
from src.prompt_builder import build_workout_prompt


def _request(**overrides: object) -> WorkoutRequest:
    defaults: dict[str, object] = {
        "fitness_goal": "Lose fat",
        "experience_level": "Intermediate",
        "days_per_week": 5,
        "equipment": "Full gym",
        "limitations": "bad knees",
    }
    defaults.update(overrides)
    return WorkoutRequest(**defaults)  # type: ignore[arg-type]


def test_prompt_contains_all_structured_inputs() -> None:
    request = _request()
    prompt = build_workout_prompt(request)

    assert request.fitness_goal in prompt
    assert request.experience_level in prompt
    assert str(request.days_per_week) in prompt
    assert request.equipment in prompt
    assert request.limitations in prompt


def test_prompt_has_required_sections_in_order() -> None:
    prompt = build_workout_prompt(_request())
    sections = [
        "ROLE",
        "USER PROFILE",
        "CONSTRAINTS",
        "WORKOUT DESIGN REQUIREMENTS",
        "OUTPUT FORMAT",
        "SAFETY REQUIREMENTS",
    ]
    positions = [prompt.index(section) for section in sections]
    assert positions == sorted(positions)


def test_prompt_uses_imperative_constraint_language() -> None:
    prompt = build_workout_prompt(_request())
    assert "MUST" in prompt
    assert "Do NOT" in prompt or "NOT include" in prompt


def test_prompt_forbids_inventing_equipment() -> None:
    prompt = build_workout_prompt(_request(equipment="No equipment"))
    assert "No equipment" in prompt
    assert "invent" in prompt.lower()


def test_prompt_requests_exact_day_count() -> None:
    prompt = build_workout_prompt(_request(days_per_week=4))
    assert "EXACTLY 4" in prompt


def test_prompt_requests_structured_output_table() -> None:
    prompt = build_workout_prompt(_request())
    assert "Sets" in prompt
    assert "Reps" in prompt
    assert "Rest" in prompt


def test_prompt_includes_disclaimer_instruction_when_limitations_present() -> None:
    prompt = build_workout_prompt(_request(limitations="bad knees"))
    assert "disclaimer" in prompt.lower()
    assert "bad knees" in prompt


def test_prompt_omits_disclaimer_instruction_when_no_limitations() -> None:
    prompt = build_workout_prompt(_request(limitations=""))
    assert "Include a short" not in prompt
    assert "consult a healthcare professional" not in prompt.lower()
    assert "do not include an injury disclaimer" in prompt.lower()


def test_prompt_forbids_medical_claims() -> None:
    prompt = build_workout_prompt(_request())
    assert "medical" in prompt.lower()
    assert "NOT a medical professional" in prompt or "not a doctor" in prompt.lower()


def test_prompt_adapts_experience_language_for_beginner() -> None:
    prompt = build_workout_prompt(_request(experience_level="Beginner"))
    assert "BEGINNER" in prompt


def test_prompt_adapts_experience_language_for_advanced() -> None:
    prompt = build_workout_prompt(_request(experience_level="Advanced"))
    assert "ADVANCED" in prompt
