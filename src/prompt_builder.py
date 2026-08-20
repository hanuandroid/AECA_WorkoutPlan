"""Builds the LLM prompt for workout plan generation.

The prompt is assembled from structured WorkoutRequest fields into explicit,
imperative, sectioned instructions (ROLE / USER PROFILE / CONSTRAINTS /
WORKOUT DESIGN REQUIREMENTS / OUTPUT FORMAT / SAFETY REQUIREMENTS) rather than
concatenated into a single sentence. See .claude/rules/prompt-engineering.md.
"""

from src.models import WorkoutRequest

_EXPERIENCE_GUIDANCE: dict[str, str] = {
    "Beginner": (
        "The user is a BEGINNER. Favor fundamental, easy-to-learn movements. "
        "Include brief form cues. Keep volume and intensity conservative and "
        "prioritize building consistent habits over pushing limits."
    ),
    "Intermediate": (
        "The user is INTERMEDIATE. They know basic form. Use moderate volume "
        "and intensity, and introduce some variety and progressive overload."
    ),
    "Advanced": (
        "The user is ADVANCED. They can handle higher complexity, higher "
        "intensity techniques, and denser training. Do not over-explain basic "
        "form; focus on programming quality."
    ),
}

_GOAL_GUIDANCE: dict[str, str] = {
    "Build muscle": (
        "Optimize the plan for hypertrophy: moderate-to-high volume, rep ranges "
        "generally in the 6-15 range, adequate exercise variety per muscle group."
    ),
    "Lose fat": (
        "Optimize the plan for fat loss: keep training density high (e.g. shorter "
        "rest where appropriate, supersets/circuits if suitable for the equipment "
        "and experience level), and mention that fat loss also depends on overall "
        "diet and activity without going into medical or nutrition-prescription "
        "detail."
    ),
    "General fitness": (
        "Optimize the plan for well-rounded general fitness: a balanced mix of "
        "strength, mobility, and light conditioning work across the week."
    ),
    "Improve endurance": (
        "Optimize the plan for endurance: favor higher-rep or interval-style work, "
        "shorter rest periods, and conditioning-oriented exercise selection."
    ),
}

_SAFETY_BLOCK_WITH_LIMITATIONS = """SAFETY REQUIREMENTS
- The user has stated the following limitation: "{limitations}"
- You MUST NOT include any exercise that obviously conflicts with this stated \
limitation.
- If a common exercise for this goal would normally conflict with the limitation, \
substitute it with a safer alternative and briefly note why.
- You are NOT a medical professional. Do NOT diagnose the limitation and do NOT \
prescribe treatment for it.
- Include a short, clearly labeled disclaimer at the end of the plan stating this \
is not medical advice and the user should consult a healthcare professional about \
their limitation before starting, especially if it is a significant injury or \
medical concern.
- Do NOT silently drop this constraint. If you cannot fully avoid conflict for some \
exercise, state that explicitly rather than ignoring the limitation."""

_SAFETY_BLOCK_NO_LIMITATIONS = """SAFETY REQUIREMENTS
- The user has not reported any injuries or limitations.
- You are NOT a medical professional. Do NOT diagnose, and do NOT make medical \
claims about the plan being medically appropriate or medically reviewed.
- Do NOT include an injury disclaimer since none was requested — keep the output \
focused on the workout plan itself."""


def build_workout_prompt(request: WorkoutRequest) -> str:
    """Build a sectioned, constraint-explicit prompt from a structured request.

    The prompt instructs the model to respect every constraint (equipment,
    limitations, day count), produce a structured weekly plan, and stay within
    a non-medical scope. See .claude/rules/prompt-engineering.md for the
    checklist this function is designed to satisfy.
    """
    role_section = _build_role_section()
    profile_section = _build_profile_section(request)
    constraints_section = _build_constraints_section(request)
    design_section = _build_design_requirements_section(request)
    output_section = _build_output_format_section(request)
    safety_section = _build_safety_section(request)

    return "\n\n".join(
        [
            role_section,
            profile_section,
            constraints_section,
            design_section,
            output_section,
            safety_section,
        ]
    )


def _build_role_section() -> str:
    return (
        "ROLE\n"
        "You are an experienced, safety-conscious personal trainer. You design "
        "practical, personalized weekly workout plans that a real person can "
        "actually follow. You are not a doctor and you never provide medical advice."
    )


def _build_profile_section(request: WorkoutRequest) -> str:
    limitations_line = (
        request.limitations.strip() if request.has_limitations else "None reported"
    )
    return (
        "USER PROFILE\n"
        f"- Fitness goal: {request.fitness_goal}\n"
        f"- Experience level: {request.experience_level}\n"
        f"- Training days available per week: {request.days_per_week}\n"
        f"- Equipment access: {request.equipment}\n"
        f"- Injuries / limitations: {limitations_line}"
    )


def _build_constraints_section(request: WorkoutRequest) -> str:
    limitation_line = (
        f'- The user has this limitation: "{request.limitations.strip()}". '
        "You MUST NOT include exercises that obviously conflict with it."
        if request.has_limitations
        else "- The user reported no limitations. Do not invent any."
    )
    return (
        "CONSTRAINTS\n"
        "You MUST respect every constraint below. Do NOT ignore, soften, or "
        "silently drop any of them.\n"
        f"- The plan MUST contain EXACTLY {request.days_per_week} training day(s) "
        f"per week, no more and no fewer.\n"
        f"- The user's available equipment is: {request.equipment}. You MUST NOT "
        "invent or assume any equipment the user does not have. Every exercise "
        "must be performable with only this equipment (or bodyweight, if that is "
        "consistent with the equipment level).\n"
        f"{limitation_line}\n"
        "- If any constraint cannot be fully satisfied for a particular exercise, "
        "say so explicitly in the plan rather than ignoring the constraint."
    )


def _build_design_requirements_section(request: WorkoutRequest) -> str:
    experience_guidance = _EXPERIENCE_GUIDANCE[request.experience_level]
    goal_guidance = _GOAL_GUIDANCE[request.fitness_goal]
    return (
        "WORKOUT DESIGN REQUIREMENTS\n"
        f"- {experience_guidance}\n"
        f"- {goal_guidance}\n"
        "- Assign each training day a specific focus (e.g. Upper Body, Lower Body, "
        "Full Body, Push, Pull, Legs, Conditioning) that makes sense for the "
        f"number of days ({request.days_per_week}) and the stated goal.\n"
        "- Select specific, named exercises appropriate to the equipment and "
        "experience level. Do NOT give generic, vague advice like 'do some squats' "
        "— name the exact exercise, e.g. 'Goblet Squat' or 'Bodyweight Squat'.\n"
        "- For each training day, include a brief warm-up guidance line before the "
        "exercises.\n"
        "- Include brief rest/recovery guidance for the days of the week that are "
        "not training days.\n"
        "- Avoid producing a plan that could apply to any random user — tie "
        "exercise selection, volume, and intensity explicitly to this user's goal, "
        "experience, and equipment."
    )


def _build_output_format_section(request: WorkoutRequest) -> str:
    header = (
        "OUTPUT FORMAT\n"
        "Return the plan in Markdown using EXACTLY this structure:\n\n"
        "# Weekly Workout Plan\n\n"
        "## Weekly Overview\n"
        "(1-2 sentences summarizing the week's structure and how it fits the "
        "user's goal)\n\n"
        "## Day 1 - <Focus>\n"
        "Warm-up: <brief warm-up guidance>\n\n"
        "| Exercise | Sets | Reps | Rest |\n"
        "|---|---|---|---|\n"
        "| <exercise name> | <sets> | <reps> | <rest, e.g. 60 sec> |\n\n"
        f"(repeat the 'Day N - <Focus>' section for EXACTLY "
        f"{request.days_per_week} training day(s) total)\n\n"
        "## Rest & Recovery\n"
        "(guidance for the non-training days of the week)\n\n"
    )
    if request.has_limitations:
        footer = (
            "## Safety Note\n"
            "(the concise disclaimer described in SAFETY REQUIREMENTS below — "
            "this section IS required because the user reported a limitation)\n\n"
        )
    else:
        footer = (
            "The plan ends after the '## Rest & Recovery' section. Do NOT add a "
            "'## Safety Note' heading or any other heading after it — the user "
            "reported no limitations, so there is nothing to disclaim.\n\n"
        )
    return (
        header
        + footer
        + "Do not include any text outside this structure. Do not return a single "
        "wall-of-text paragraph."
    )


def _build_safety_section(request: WorkoutRequest) -> str:
    if request.has_limitations:
        return _SAFETY_BLOCK_WITH_LIMITATIONS.format(
            limitations=request.limitations.strip()
        )
    return _SAFETY_BLOCK_NO_LIMITATIONS
