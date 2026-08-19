---
name: prompt-design
description: Workflow for designing and iterating on the workout-generation prompt in src/prompt_builder.py against representative user profiles until constraints are consistently respected. Use when creating or improving the workout prompt.
---

# Prompt Design Workflow

This skill teaches Claude Code how to design and improve the prompt in
`src/prompt_builder.py`. It is a development-time workflow, not part of the running
application. Follow `.claude/rules/prompt-engineering.md` and
`.claude/rules/safety.md` as the standing requirements; this skill is the process for
meeting them.

## Workflow

1. **Identify user inputs.** Enumerate every field on `WorkoutRequest`
   (`src/models.py`): fitness goal, experience level, days per week, equipment,
   limitations.
2. **Identify constraints.** For each field, decide what the model must never
   violate: equipment must not be invented, day count must be exact, limitations
   must not be silently dropped.
3. **Define the LLM role.** Write a one- or two-sentence `ROLE` section framing the
   model as an experienced, safety-conscious personal trainer — sets tone and scope
   without inviting medical claims.
4. **Define workout-generation rules.** Write the `WORKOUT DESIGN REQUIREMENTS`
   section: experience-appropriate complexity, equipment-scoped exercise selection,
   exact day-count structure, specificity over generic advice.
5. **Define output structure.** Write the `OUTPUT FORMAT` section: weekly overview,
   warm-up guidance, `Day N – Focus` sections each with an exercise/sets/reps/rest
   table, recovery guidance, conditional safety note.
6. **Define safety behavior.** Write the `SAFETY REQUIREMENTS` section: no
   diagnosis/treatment claims; disclaimer required only when `limitations` is
   non-empty.
7. **Test against multiple user profiles.** Build the prompt for each profile below
   and read the resulting prompt text (and, if a `GROQ_API_KEY` is available, the
   actual model output).
8. **Identify constraint violations.** Check each output against the profile's
   expectations (see below). Common failure modes: wrong equipment used, wrong
   number of days, limitation ignored, disclaimer missing/present incorrectly,
   generic/interchangeable-sounding plan across profiles.
9. **Improve the prompt.** Tighten imperative language exactly where a violation
   occurred — don't rewrite unrelated sections that are already working.
10. **Repeat** until constraints are consistently respected across all three
    profiles, then add/update the corresponding unit test in
    `tests/test_prompt_builder.py` so the fix is locked in.

## Test profiles

### Profile A — beginner muscle-building, minimal equipment
- Goal: Build muscle
- Experience: Beginner
- Days: 3
- Equipment: Home dumbbells
- Limitations: None

Expect: beginner-appropriate exercises (fundamental movements, more coaching cues),
dumbbell-only exercises, exactly 3 training days, no injury disclaimer.

### Profile B — intermediate fat-loss with a physical limitation
- Goal: Lose fat
- Experience: Intermediate
- Days: 5
- Equipment: Full gym
- Limitations: Bad knees

Expect: knee limitation explicitly respected (no obviously knee-stressing movements
without modification), no conflicting exercises, exactly 5 training days, a concise
safety disclaimer present.

### Profile C — beginner general fitness, no equipment, specific exclusion
- Goal: General fitness
- Experience: Beginner
- Days: 2
- Equipment: No equipment
- Limitations: No overhead pressing

Expect: bodyweight-only plan, exactly 2 training days, no overhead-pressing
movements anywhere in the plan, beginner-appropriate complexity, a concise
disclaimer referencing the limitation.

## Verifying adaptation across profiles

The three profiles should never produce interchangeable output. If Profile A and
Profile C's plans read as the same generic bodyweight/dumbbell plan with only the
day count changed, the prompt is not adapting to goal/experience — strengthen the
`WORKOUT DESIGN REQUIREMENTS` section to explicitly tie exercise selection and
volume/intensity language to the stated goal and experience level, not just
equipment and days.

## Note on live evaluation

Building the prompt string requires no API key (`build_workout_prompt` is pure text
construction). Evaluating actual model *compliance* requires a live `GROQ_API_KEY`.
When no key is available, validate as much as possible via
`tests/test_prompt_builder.py` (presence of required content and imperative
language) and document remaining live-verification as a manual step — see Phase 12
in `docs/IMPLEMENTATION_PLAN.md`.
