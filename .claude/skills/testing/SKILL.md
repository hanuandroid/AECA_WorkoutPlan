---
name: testing
description: Testing workflow for the Workout Plan Generator — runs and extends unit tests for validation, prompt generation, and mocked Groq API error handling. Use when asked to run tests, add test coverage, or verify the app before completion.
---

# Testing Workflow

Follow `.claude/rules/testing.md` for the standing test requirements. This skill is
the step-by-step process for running and extending the test suite.

## Steps

1. **Run unit tests.**
   ```
   pytest -q
   ```
   Report pass/fail counts and any failures with their assertion output.

2. **Confirm validation coverage.** `tests/test_validator.py` must cover: valid
   request, 1 day, 7 days, 0 days, 8 days, missing goal, missing experience, missing
   equipment. If any case is missing, add it (see
   `.claude/skills/workout-validation/SKILL.md`).

3. **Confirm prompt-generation coverage.** `tests/test_prompt_builder.py` must
   assert the built prompt contains goal, experience, days, equipment, and
   (conditionally) limitations, plus explicit constraint-respecting instructions. If
   any assertion is missing, add it (see `.claude/skills/prompt-design/SKILL.md`).

4. **Confirm Groq calls are mocked everywhere.** Grep the test suite for any
   reference to a real API key or live network call — there should be none. All
   Groq SDK interaction in tests goes through `unittest.mock.patch` at the
   `src/groq_client.py` boundary.

5. **Confirm API failure coverage.** `tests/test_groq_client.py` and
   `tests/test_workout_service.py` must cover: authentication failure, network
   error, timeout, empty response, malformed response — each resulting in a friendly
   error surfaced through `ServiceResult`, never an unhandled exception.

6. **Report failures clearly.** For each failing test: file, test name, expected vs.
   actual, and a one-line diagnosis of whether the bug is in the test or in the
   source it's testing. Fix test bugs directly; report source bugs rather than
   loosening assertions to force a pass.

7. **Optional: syntax/startup check.** `python -m py_compile app.py src/*.py` to
   catch syntax errors, and `python -c "import app"` style checks are not reliable
   for Streamlit (it needs `streamlit run`) — prefer `python -m py_compile` plus the
   test suite as the pre-submission gate. See Phase 15 of
   `docs/IMPLEMENTATION_PLAN.md` for the full final-verification checklist.
