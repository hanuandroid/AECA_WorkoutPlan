# Implementation Plan — Workout Plan Generator

## 1. Assignment Requirements (source: `AI Engineering Cohort - Assignment.pdf`)

Build a single-page Streamlit app that:

1. Collects **structured inputs**, not a single free-text box:
   - Fitness goal — dropdown: Build muscle / Lose fat / General fitness / Improve endurance
   - Experience level — dropdown: Beginner / Intermediate / Advanced
   - Days available per week — slider/number input, 1–7
   - Equipment access — dropdown/multiselect: No equipment / Home dumbbells / Full gym
   - Injuries/limitations — optional free text (e.g. "bad knees", "no overhead pressing")
2. Has a **"Generate Plan"** button that sends inputs to an LLM (Groq) and displays a
   clearly formatted weekly breakdown.
3. Has a **typed Python function** that takes structured inputs, builds a well-designed
   prompt, calls the Groq API, and returns the response — wrapped in `try/except`.
4. Has **basic error handling**:
   - Missing/invalid inputs (e.g. 0 days) → friendly message, not a crash
   - Failed API call (bad key, network issue, rate limit) → friendly message, not a crash
   - Empty/malformed LLM response → friendly fallback message

**The real learning goal is prompt design.** The prompt must not simply concatenate
inputs into a sentence. It must push the model to respect constraints (equipment,
injuries, days/week), return structured output (Day 1/Day 2… with exercises, sets,
reps), and stay appropriately scoped (no medical claims, disclaimer when injury input
is given).

Tech stack: Python (type hints, try/except), Streamlit, Groq. No mandate for any other
framework.

**Rubric:**

| Criteria | Weight |
|---|---|
| App runs without crashing on empty/invalid input | 20% |
| Inputs are structured and correctly passed into the prompt | 25% |
| Prompt design respects constraints, is well-structured, genuinely usable | 30% |
| Error handling (API failure, empty/malformed response) | 15% |
| Code quality (type hints, function separation, readability) | 10% |

Stretch goals (optional, only after the above is solid): Regenerate button, persist
last plan in `st.session_state`, download as `.txt`/`.md`, "swap this exercise"
mini-feature.

## 2. Current Repository Analysis

The repository is **completely empty** except for the assignment PDF
(`AI Engineering Cohort - Assignment.pdf`). There is:

- No existing Python code, no Streamlit app.
- No `requirements.txt` / dependency manifest.
- No `.env` / environment configuration.
- No tests.
- No `README.md`.
- Not yet a git repository.

Conclusion: this is a **greenfield build**. There is nothing to reuse or preserve —
every file listed in this plan is new. No existing implementation needs to be
respected or worked around.

## 3. Proposed Architecture

Single-page Streamlit app with a strict linear pipeline and clean separation of
concerns. No multi-agent runtime, no database, no auth, no backend server, no vector
store, no LangChain — see `.claude/rules/project.md` for the durable boundary.

```
app.py  (Streamlit UI only)
   │
   ▼
src/models.py           — WorkoutRequest dataclass (typed input contract)
   │
   ▼
src/validator.py         — validate_workout_request() -> ValidationResult
   │
   ▼
src/prompt_builder.py    — build_workout_prompt(request) -> str
   │
   ▼
src/groq_client.py       — call_groq(prompt) -> GroqResult (wraps SDK, try/except)
   │
   ▼
src/workout_service.py   — generate_workout_plan(request) -> ServiceResult
                             (orchestrates validate → build prompt → call Groq)
   │
   ▼
app.py — renders ServiceResult (success plan or friendly error) to Streamlit
```

`app.py` never talks to `validator`, `prompt_builder`, or `groq_client` directly for
the generation flow — it calls `workout_service.generate_workout_plan()` once and
renders the result. This keeps the UI file thin and keeps business logic testable
without Streamlit installed/running.

## 4. File-by-File Implementation Plan

| File | Responsibility |
|---|---|
| `app.py` | Page config, input widgets, "Generate Plan" / "Regenerate" buttons, calls `workout_service`, renders result, session-state persistence, download button. No business logic. |
| `src/__init__.py` | Package marker. |
| `src/models.py` | `WorkoutRequest` dataclass (typed fields), `FitnessGoal`/`ExperienceLevel`/`Equipment` enums (constants for fixed dropdown options), `ValidationResult`, `ServiceResult` typed result containers. |
| `src/validator.py` | `validate_workout_request(request) -> ValidationResult` — checks days 1–7, required fields non-empty, no exceptions escape. |
| `src/prompt_builder.py` | `build_workout_prompt(request) -> str` — structured, sectioned prompt (ROLE / USER PROFILE / CONSTRAINTS / WORKOUT DESIGN REQUIREMENTS / OUTPUT FORMAT / SAFETY REQUIREMENTS). |
| `src/groq_client.py` | `GroqClientError` exception, `call_groq(prompt, model=...) -> str` — reads `GROQ_API_KEY` from env via `python-dotenv`/`os.environ`, wraps SDK call in try/except, raises `GroqClientError` with a friendly message on failure (never leaks stack traces). |
| `src/workout_service.py` | `generate_workout_plan(request) -> ServiceResult` — orchestrates validate → build prompt → call Groq → check for empty/malformed response → returns success or friendly error, all exceptions caught here so `app.py` never needs a raw `try/except` around business logic. |
| `tests/test_validator.py` | Validation edge cases. |
| `tests/test_prompt_builder.py` | Prompt contains all structured inputs + explicit constraint language. |
| `tests/test_groq_client.py` | Mocked Groq SDK — success, auth failure, network error, timeout, empty response. |
| `tests/test_workout_service.py` | End-to-end orchestration with mocked Groq client — invalid input short-circuits before any API call, API failure surfaces friendly error, malformed/empty response surfaces friendly fallback. |
| `requirements.txt` | `streamlit`, `groq`, `python-dotenv`. Nothing else. |
| `.env.example` | `GROQ_API_KEY=your_groq_api_key_here` |
| `.gitignore` | `.env`, `__pycache__/`, `.venv/`, etc. |
| `README.md` | Full documentation per Phase 14. |

## 5. Prompt-Engineering Strategy

The prompt is the graded core of this assignment (30%). Strategy:

1. **Sectioned system+user prompt**, not a concatenated sentence. Sections: `ROLE`,
   `USER PROFILE`, `CONSTRAINTS`, `WORKOUT DESIGN REQUIREMENTS`, `OUTPUT FORMAT`,
   `SAFETY REQUIREMENTS`. Each section is built from the structured `WorkoutRequest`
   fields, not from a single formatted string the caller passes in.
2. **Explicit, imperative constraint language** — "You MUST", "Do NOT invent
   equipment the user does not have", "Do NOT include exercises that conflict with
   the stated limitation" — rather than descriptive/passive phrasing the model can
   deprioritize.
3. **Conditional safety block** — the `SAFETY REQUIREMENTS` section only asks for an
   injury disclaimer when `limitations` is non-empty, so plans without limitations
   don't carry a meaningless boilerplate warning (tested explicitly).
4. **Day-count enforcement** — the prompt states the exact number of training days
   required and instructs the model to produce exactly that many `Day N` sections,
   including rest-day guidance for the remaining days of the week.
5. **Equipment-scoped exercise selection** — the prompt enumerates the exact
   equipment available and forbids substitutions outside that list.
6. **Experience-scaled complexity** — beginner → fundamental movements, more
   guidance, more conservative volume; advanced → higher complexity/intensity
   language, less hand-holding.
7. **Structured output contract** — the prompt specifies a Markdown template
   (weekly overview, warm-up guidance, `Day N – Focus` sections with an
   exercise/sets/reps/rest table, recovery guidance, optional safety note) so the
   response is predictable enough to render directly in Streamlit.
8. **No medical scope** — the prompt explicitly forbids diagnosis or treatment
   claims and frames any injury accommodation as "avoid obvious conflicts", not
   medical judgment.

Iteration loop (also documented as the `.claude/skills/prompt-design` skill): run the
three assignment test profiles (Profiles A/B/C, Phase 12 test scenarios), inspect the
output for constraint violations (wrong equipment, wrong day count, ignored
limitation, missing disclaimer), tighten the imperative language where violated,
re-test. This requires a live `GROQ_API_KEY`, which is not present in this
environment — the strategy and structural checks are validated via unit tests against
the prompt *text* (does it contain the required imperative constraints, day count,
equipment list, disclaimer instruction), and the live-model iteration is documented
as a manual step for whoever runs this with a real key (see Section 11, Risks).

## 6. Validation Strategy

`src/validator.py` never raises out to the caller. `validate_workout_request`:

- `days_per_week` must be an int in `[1, 7]` inclusive — 0, 8, negative, or
  non-numeric values are rejected.
- `fitness_goal`, `experience_level`, `equipment` must be non-empty and one of the
  allowed constants from `src/models.py`.
- `limitations` is optional; empty string/`None` is valid.
- Returns a `ValidationResult(is_valid: bool, errors: list[str])` — `app.py` renders
  `errors` via `st.error` and never calls the service layer when invalid.

## 7. Error-Handling Strategy

Three independent failure surfaces, each caught at the layer that owns it so no raw
exception or stack trace ever reaches Streamlit:

1. **Input errors** — caught by `validator` before any network call; rendered as
   `st.error` list in `app.py`.
2. **Groq/API errors** — `groq_client.call_groq` catches SDK/network exceptions
   (auth failure, connection error, timeout, rate limit) and re-raises a single
   `GroqClientError` with a friendly message; original exception is logged via
   `logging` (message + type only, never the API key) for debugging.
3. **Empty/malformed response** — `workout_service` checks the returned text is
   non-empty and minimally well-formed (contains at least one `Day` heading) before
   declaring success; otherwise returns a `ServiceResult` with the fallback message
   "Sorry, I couldn't generate a workout plan right now. Please try again."

`app.py` has exactly one `try/except` boundary as a last-resort safety net around the
`generate_workout_plan` call, even though `workout_service` is designed not to leak
exceptions — defense in depth, not the primary mechanism.

## 8. Testing Strategy

`pytest`, no real API key required — all Groq calls mocked via `unittest.mock`.

- **Validation**: valid request, 1 day, 7 days, 0 days, 8 days, missing goal, missing
  experience, missing equipment.
- **Prompt generation**: asserts goal/experience/days/equipment/limitations text
  present; asserts explicit constraint-respecting instructions present; asserts
  disclaimer instruction present only when limitations given.
- **Groq client**: mocked success, auth failure, network/connection error, timeout,
  empty response — each maps to a friendly `GroqClientError`, never an unhandled
  exception.
- **Service orchestration**: invalid input short-circuits before calling Groq; Groq
  failure and malformed/empty response both surface friendly `ServiceResult` errors.

## 9. Stretch-Goal Strategy

Implemented only after core requirements are complete and tested, and only if they
don't add risk to the core flow:

1. **Regenerate** — re-invokes `generate_workout_plan` with the same request (Groq
   sampling naturally varies output; no extra plumbing needed beyond a second button
   calling the same service function).
2. **Session-state persistence** — last `ServiceResult`/`WorkoutRequest` stored in
   `st.session_state` so results survive Streamlit reruns.
3. **Download as `.txt`/`.md`** — `st.download_button` over the plan text already
   held in session state.

**Not implemented**: "Swap this exercise" — explicitly optional and lowest priority
per the assignment; adds parsing complexity (would require structured/JSON output or
per-exercise re-prompting) disproportionate to a stretch goal, and is called out in
the brief as something to skip unless the core is already stable.

## 10. Acceptance Criteria

- [ ] App starts with `streamlit run app.py` without error (given a valid or absent
      `GROQ_API_KEY` — absent key should fail gracefully only when Generate is
      clicked, not at startup).
- [ ] All five structured inputs are present and required ones are validated.
- [ ] 0 days, 8 days, and missing-field submissions show a friendly `st.error` and do
      not call the Groq API.
- [ ] Prompt sent to Groq contains every structured field and explicit, imperative
      constraint language for equipment/injuries/day-count.
- [ ] Groq auth failure, network error, timeout, and empty response each render a
      friendly Streamlit message, never a stack trace.
- [ ] Generated plan renders as a structured weekly breakdown (day/focus/exercises/
      sets/reps/rest), not a wall of text.
- [ ] Safety disclaimer appears when limitations are provided and is absent when they
      are not (verified by prompt-text test; final behavior depends on model
      compliance).
- [ ] `pytest` passes fully with no real network/API access.
- [ ] No API key is hardcoded anywhere in source; `.env.example` present, real `.env`
      gitignored.
- [ ] `README.md` covers setup, running, testing, prompt approach, rubric
      self-assessment.

## 11. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| No `GROQ_API_KEY` available in this environment to live-test the prompt against Groq | Validate prompt *construction* thoroughly with unit tests (all required content present); document the three Phase-12 test profiles in the `prompt-design` skill and README as a manual verification checklist for whoever has a key; keep constraint language maximally explicit to reduce first-try drift risk. |
| LLM ignores a constraint (e.g. suggests overhead press despite exclusion) | Imperative, itemized constraint list in its own `CONSTRAINTS` section; explicit negative instructions ("Do NOT include X"); acceptable residual risk documented in README limitations — no mechanical way to force compliance from a text-completion API without output parsing/rejection, which is out of scope for this assignment size. |
| Groq SDK/model name changes over time | Model name is a single constant in `groq_client.py`, easy to update; not hardcoded inline in multiple places. |
| Over-engineering (multi-agent runtime, DB, auth) creeping into the app | `.claude/rules/project.md` explicitly forbids these; architecture stays a single linear pipeline per Section 3. |
| Secrets leaking into git | `.env` in `.gitignore`; only `.env.example` committed; `groq_client.py` reads via `os.environ`/`python-dotenv`, never a literal string. |
| Windows path/shell quirks during dev | Confirmed working directory and tool usage account for PowerShell/Bash split already present in this environment. |
