---
name: workout-validation
description: Reusable validation workflow for the workout request inputs (goal, experience, days, equipment, limitations) so invalid input produces friendly errors instead of exceptions reaching the UI. Use when implementing or changing src/validator.py.
---

# Workout Request Validation Workflow

This skill defines how `src/validator.py` validates a `WorkoutRequest`
(`src/models.py`) before it reaches the prompt builder or the Groq client. Goal:
invalid input always produces a friendly, user-facing error — never an exception
that reaches `app.py` unhandled.

## Fields to validate

- **fitness_goal** — required; must be one of the allowed constants (Build muscle /
  Lose fat / General fitness / Improve endurance).
- **experience_level** — required; must be one of the allowed constants (Beginner /
  Intermediate / Advanced).
- **days_per_week** — required; must be an integer between 1 and 7 inclusive.
- **equipment** — required; must be one of the allowed constants (No equipment /
  Home dumbbells / Full gym).
- **limitations** — optional; empty string or `None` is valid; if present, treated
  as free text and passed through to the prompt builder unmodified (no need to
  validate its content).

## Rules

- `days_per_week` must be between 1 and 7. 0, negative numbers, values above 7, and
  non-integer values are all invalid.
- Every required field above must be non-empty and match one of its allowed values —
  reject empty strings, `None`, and values outside the allowed set (defends against
  a UI bug passing something unexpected, not just user error).
- Validation never raises. It returns a result object (`ValidationResult` in
  `src/models.py`) with `is_valid: bool` and `errors: list[str]`, where each error
  string is friendly and specific enough for `st.error()` (e.g. "Please select at
  least 1 day per week." rather than "ValueError: days_per_week out of range").
- Collect all validation errors in one pass rather than stopping at the first
  failure, so the user sees every problem with their input at once.
- `limitations` never causes a validation failure — it is optional by design.

## Workflow when implementing or changing validation

1. Add/update the check in `src/validator.py`.
2. Add the corresponding friendly error message as a constant, not an inline string
   duplicated across checks.
3. Add or update the matching test case in `tests/test_validator.py` — every rule
   above must have at least one passing and one failing test case.
4. Confirm `app.py` never calls `workout_service.generate_workout_plan()` when
   `ValidationResult.is_valid` is `False` — validation must gate the entire pipeline,
   not just get logged.
