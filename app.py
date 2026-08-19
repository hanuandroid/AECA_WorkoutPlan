"""Streamlit UI for the Workout Plan Generator.

This file is responsible only for page setup, input widgets, calling the
workout_service orchestration layer, and rendering the result. No validation,
prompt-building, or API-access logic lives here - see src/.
"""

import streamlit as st
from dotenv import load_dotenv

from src.models import (
    EQUIPMENT_OPTIONS,
    EXPERIENCE_LEVELS,
    FITNESS_GOALS,
    MAX_DAYS_PER_WEEK,
    MIN_DAYS_PER_WEEK,
    ServiceResult,
    WorkoutRequest,
)
from src.workout_service import UNEXPECTED_ERROR_MESSAGE, generate_workout_plan

load_dotenv()

PAGE_TITLE = "Workout Plan Generator"
PLAN_STATE_KEY = "last_plan_result"
REQUEST_STATE_KEY = "last_request"


def configure_page() -> None:
    st.set_page_config(page_title=PAGE_TITLE, page_icon="🏋️", layout="centered")
    st.title("🏋️ Workout Plan Generator")
    st.caption(
        "Tell us about yourself and get a personalized weekly workout plan. "
        "This tool does not provide medical advice — consult a healthcare "
        "professional for any injury or medical concern."
    )


def collect_user_input() -> WorkoutRequest:
    fitness_goal = st.selectbox("Fitness goal", options=FITNESS_GOALS)
    experience_level = st.selectbox("Experience level", options=EXPERIENCE_LEVELS)
    days_per_week = st.slider(
        "Days available per week",
        min_value=MIN_DAYS_PER_WEEK,
        max_value=MAX_DAYS_PER_WEEK,
        value=3,
    )
    equipment = st.selectbox("Equipment access", options=EQUIPMENT_OPTIONS)
    limitations = st.text_input(
        "Injuries or limitations (optional)",
        placeholder='e.g. "bad knees" or "no overhead pressing"',
    )

    return WorkoutRequest(
        fitness_goal=fitness_goal,
        experience_level=experience_level,
        days_per_week=days_per_week,
        equipment=equipment,
        limitations=limitations,
    )


def run_generation(request: WorkoutRequest) -> None:
    with st.spinner("Designing your workout plan..."):
        try:
            result = generate_workout_plan(request)
        except Exception:  # noqa: BLE001 - defense in depth, service should not raise
            result = ServiceResult(success=False, error_message=UNEXPECTED_ERROR_MESSAGE)

    st.session_state[PLAN_STATE_KEY] = result
    st.session_state[REQUEST_STATE_KEY] = request


def render_result() -> None:
    result: ServiceResult | None = st.session_state.get(PLAN_STATE_KEY)
    if result is None:
        return

    if not result.success:
        st.error(result.error_message)
        return

    st.success("Your plan is ready!")
    st.markdown(result.plan_text)
    st.download_button(
        "Download plan (.md)",
        data=result.plan_text,
        file_name="workout_plan.md",
        mime="text/markdown",
    )


def main() -> None:
    configure_page()
    request = collect_user_input()

    col_generate, col_regenerate = st.columns(2)
    generate_clicked = col_generate.button("Generate Plan", type="primary")
    regenerate_clicked = col_regenerate.button(
        "Regenerate", disabled=REQUEST_STATE_KEY not in st.session_state
    )

    if generate_clicked:
        run_generation(request)
    elif regenerate_clicked:
        previous_request = st.session_state[REQUEST_STATE_KEY]
        run_generation(previous_request)

    render_result()


if __name__ == "__main__":
    main()
