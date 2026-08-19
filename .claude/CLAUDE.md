# Workout Plan Generator — Project Instructions

This is an AI Engineering Cohort assignment. The primary learning objective is
**prompt engineering**, not architecture. Read `docs/IMPLEMENTATION_PLAN.md` before
making structural changes.

## Stack

- Python 3.x with type hints on every function signature.
- Streamlit for the UI.
- Groq for the LLM call.
- No other frameworks unless the task genuinely cannot be done without one.

## Code standards

- Type hints are required on all function parameters and return values.
- Code must be readable and maintainable over clever or terse.
- Keep functions small and focused on one responsibility.
- Do not introduce unnecessary frameworks, abstractions, or dependencies.
- Keep UI code (`app.py`) separate from validation, prompt-building, and API-access
  code (`src/`).

## Secrets

- Never hardcode API keys or other secrets in source.
- Read secrets from environment variables (`.env` via `python-dotenv`, gitignored).
- `.env.example` documents required variables with placeholder values only.

## Error handling

- Handle errors gracefully at the layer that owns them (input validation, API call,
  response parsing). No raw exception or stack trace should ever reach the Streamlit
  UI.
- Use specific exception types and meaningful messages; avoid bare `except:`.

## Prompt engineering

- Prompt constraints must be explicit and imperative, not implied.
- The prompt must never simply concatenate user inputs into a sentence — see
  `.claude/rules/prompt-engineering.md`.
- No medical diagnosis or medical claims in generated content — see
  `.claude/rules/safety.md`.

## Testing

- Validation logic and prompt generation require tests.
- Tests must not require a real Groq API key — mock external calls.

## Scope discipline

- Preserve the assignment scope: a single-page Streamlit app with a linear
  pipeline (UI → validation → prompt builder → Groq client → output). See
  `.claude/rules/project.md` for explicit architecture boundaries.
- Do not turn the application itself into a multi-agent system. The `.claude/agents`
  and `.claude/skills` in this repo are development-time tools for building and
  reviewing the app — they are not part of the application's runtime architecture.
