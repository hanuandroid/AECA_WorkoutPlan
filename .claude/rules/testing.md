# Testing Rules

- Validation logic (`src/validator.py`) requires tests covering valid input and every
  edge case (0 days, 8 days, missing required fields).
- Prompt construction (`src/prompt_builder.py`) requires tests that assert the
  built prompt contains every structured input and the explicit constraint
  instructions described in `.claude/rules/prompt-engineering.md`.
- Error handling requires tests for: API authentication failure, network/connection
  error, timeout, empty response, malformed response.
- Missing/invalid inputs require tests proving the service layer short-circuits
  before any API call is attempted.
- Tests must not require a real Groq API key or network access. Mock the Groq SDK
  client (`unittest.mock.patch`) at the boundary in `src/groq_client.py`.
- Prefer `pytest` with plain `assert` statements; keep tests fast and hermetic.
- Test file names mirror the module under test: `tests/test_validator.py`,
  `tests/test_prompt_builder.py`, `tests/test_groq_client.py`,
  `tests/test_workout_service.py`.
