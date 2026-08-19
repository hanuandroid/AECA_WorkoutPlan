# Project Rules — Scope & Architecture Boundaries

## Assignment scope

This is a single-page Streamlit app that collects structured fitness inputs and
generates a personalized weekly workout plan via the Groq API. The deliverable is
graded primarily on prompt design, structured inputs, reliability, and error
handling — not on architectural sophistication. See `docs/IMPLEMENTATION_PLAN.md`
for the full rubric mapping.

## Architecture boundaries

The application is a strict linear pipeline:

```
Streamlit UI (app.py)
  -> Validation (src/validator.py)
  -> Prompt Builder (src/prompt_builder.py)
  -> Groq Client (src/groq_client.py)
  -> Workout Service orchestration (src/workout_service.py)
  -> Streamlit output (app.py)
```

- **UI, validation, prompt generation, and API access are separate modules.** Do not
  merge them into one file or one function.
- `app.py` contains only Streamlit page setup, widgets, and rendering. It calls
  `workout_service.generate_workout_plan()` and nothing lower in the stack directly
  for the generation flow.

## Explicitly out of scope — do not add

- No unnecessary abstraction layers, factories, or plugin systems for a single-LLM,
  single-form app.
- No database of any kind (SQL or otherwise) — nothing here needs persistence beyond
  `st.session_state` for the current browser session.
- No authentication/login system.
- No backend server (Flask/FastAPI/etc.) — Streamlit is the entire application.
- No vector database or embeddings — there is no retrieval requirement in this
  assignment.
- No LangChain or other LLM orchestration framework unless a specific requirement
  proves genuinely impossible without one (it won't for this assignment — a single
  Groq chat-completion call is sufficient).
- No multi-agent runtime inside the application. The `.claude/agents` in this repo
  are development-time reviewers for Claude Code; they must never be reflected in
  `app.py` or `src/` as an in-app agent framework.

If a change seems to require any of the above, stop and reconsider the approach
before implementing — it is very likely scope creep for this assignment.
