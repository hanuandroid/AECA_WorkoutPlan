"""Orchestrates the workout plan generation pipeline.

validate -> build prompt -> call Groq -> validate response -> ServiceResult

This is the only module app.py calls for the generation flow. No exception
should ever escape generate_workout_plan.
"""

import logging

from src.groq_client import GroqClientError, call_groq
from src.models import ServiceResult, WorkoutRequest
from src.prompt_builder import build_workout_prompt
from src.validator import validate_workout_request

logger = logging.getLogger(__name__)

EMPTY_RESPONSE_MESSAGE = (
    "Sorry, I couldn't generate a workout plan right now. Please try again."
)
UNEXPECTED_ERROR_MESSAGE = (
    "Something unexpected went wrong while generating your plan. Please try again."
)

# A minimally well-formed plan should contain at least one day heading.
_DAY_HEADING_MARKER = "Day 1"


def generate_workout_plan(request: WorkoutRequest) -> ServiceResult:
    """Validate, prompt, and generate a workout plan for the given request.

    Returns a ServiceResult on every path - never raises - so app.py can
    render either the plan or a friendly error message unconditionally.
    """
    validation = validate_workout_request(request)
    if not validation.is_valid:
        return ServiceResult(
            success=False, error_message=" ".join(validation.errors)
        )

    prompt = build_workout_prompt(request)

    try:
        plan_text = call_groq(prompt)
    except GroqClientError as exc:
        return ServiceResult(success=False, error_message=str(exc))
    except Exception:  # noqa: BLE001 - last-resort safety net, never leak a trace
        logger.exception("Unexpected error while calling Groq")
        return ServiceResult(success=False, error_message=UNEXPECTED_ERROR_MESSAGE)

    if not _is_well_formed_plan(plan_text):
        logger.warning("Groq returned an empty or malformed plan")
        return ServiceResult(success=False, error_message=EMPTY_RESPONSE_MESSAGE)

    return ServiceResult(success=True, plan_text=plan_text)


def _is_well_formed_plan(plan_text: str) -> bool:
    stripped = plan_text.strip()
    if not stripped:
        return False
    return _DAY_HEADING_MARKER in stripped
