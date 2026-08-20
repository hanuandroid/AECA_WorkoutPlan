# Workout Plan Generator

A single-page Streamlit app that collects structured fitness information and
generates a personalized weekly workout plan using an LLM via the [Groq
API](https://groq.com/). Built for the AI Engineering Cohort assignment — the
primary focus is **prompt design**, not architecture.

> ⚠️ This app does not provide medical advice. It does not diagnose injuries or
> prescribe treatment. If you have a significant injury or medical concern,
> consult a healthcare professional before starting any workout plan.

## 1. Project Overview

You tell the app your fitness goal, experience level, available training days,
equipment, and any injuries/limitations. It builds a detailed, constraint-aware
prompt, sends it to a Groq-hosted LLM, and renders the result as a structured
weekly plan — not a generic wall of text.

## 2. Features

- Structured inputs: goal, experience, days/week, equipment, optional limitations.
- One-click plan generation with a clearly formatted, day-by-day Markdown output.
- Regenerate button for a different variation of the same request.
- Last plan persisted in `st.session_state` across reruns.
- Download the plan as a `.md` file.
- Friendly error handling for invalid input, API failures, and empty/malformed
  responses — the app never crashes or shows a raw stack trace.

## 3. Architecture

Strict linear pipeline, no multi-agent runtime, no database, no backend server:

```
app.py (Streamlit UI)
  -> src/validator.py        (validate structured input)
  -> src/prompt_builder.py   (build the sectioned LLM prompt)
  -> src/groq_client.py      (call Groq, translate failures to friendly errors)
  -> src/workout_service.py  (orchestrates the above end to end)
  -> app.py                  (render plan or friendly error)
```

| File | Responsibility |
|---|---|
| `app.py` | Streamlit UI only — widgets, buttons, rendering. |
| `src/models.py` | Typed data models: `WorkoutRequest`, `ValidationResult`, `ServiceResult`, and the fixed dropdown constants. |
| `src/validator.py` | Validates a `WorkoutRequest`; never raises. |
| `src/prompt_builder.py` | Builds the sectioned, constraint-explicit LLM prompt. |
| `src/groq_client.py` | Thin Groq SDK wrapper; translates every failure mode into a friendly `GroqClientError`. |
| `src/workout_service.py` | Orchestrates validate → prompt → call → check response. |

See `docs/IMPLEMENTATION_PLAN.md` for the full design rationale, and `.claude/`
for the development-time rules, agents, and skills used to build and review
this project (these are Claude Code tooling, not part of the running app).

## 4. Installation

Requires Python 3.10+.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## 5. Environment Setup

Copy the example env file and fill in your key:

```bash
cp .env.example .env
```

## 6. Groq API Key Configuration

1. Create a free API key at [console.groq.com](https://console.groq.com/keys).
2. Put it in `.env`:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```
3. Never commit `.env` — it's gitignored. Only `.env.example` (with a placeholder)
   is committed.
4. Optional: set `GROQ_MODEL` in `.env` to override the default model
   (`openai/gpt-oss-20b`). Groq's catalog of active models changes over time and
   varies by account/plan — if plan generation fails with a friendly error, it's
   most often a 404 "model_not_found" from an outdated model name. Check
   [console.groq.com/docs/models](https://console.groq.com/docs/models) (or call
   `client.models.list()`) for a model your account can access, then set
   `GROQ_MODEL` accordingly — no code change needed.

## 7. How to Run

```bash
streamlit run app.py
```

The app starts and renders even without a valid API key — the key is only
required when you click **Generate Plan**, at which point a missing/invalid key
produces a friendly error rather than a crash.

## 8. Example Inputs

- Goal: `Build muscle`
- Experience: `Beginner`
- Days available: `3`
- Equipment: `Home dumbbells`
- Limitations: *(leave blank)*

## 9. Example Output (abridged)

```markdown
# Weekly Workout Plan

## Weekly Overview
A 3-day full-body dumbbell split for a beginner focused on building muscle...

## Day 1 - Full Body
Warm-up: 5 minutes light cardio + bodyweight squats and arm circles

| Exercise | Sets | Reps | Rest |
|---|---|---|---|
| Goblet Squat | 3 | 10 | 60 sec |
| Dumbbell Row | 3 | 10 | 60 sec |
| Dumbbell Shoulder Press | 3 | 10 | 60 sec |

## Rest & Recovery
On non-training days, prioritize sleep and light walking...
```

## 10. Error Handling

| Scenario | Behavior |
|---|---|
| 0 days / 8 days / missing goal, experience, or equipment | Friendly `st.error` message; the Groq API is never called. |
| Missing/invalid `GROQ_API_KEY` | Friendly message asking to configure the key. |
| Network error / timeout / rate limit / auth failure | Friendly, failure-specific message. No stack trace shown. |
| Empty or malformed LLM response | "Sorry, I couldn't generate a workout plan right now. Please try again." |

## 11. Testing

```bash
pytest -q
```

40 tests, no real `GROQ_API_KEY` or network access required — all Groq SDK calls
are mocked with `unittest.mock`. Coverage:

- **Validation** — valid request, 1/7 day boundaries, 0/8 day rejection, missing
  goal/experience/equipment, limitations optional.
- **Prompt generation** — every structured input appears in the built prompt;
  required sections (`ROLE`/`USER PROFILE`/`CONSTRAINTS`/`WORKOUT DESIGN
  REQUIREMENTS`/`OUTPUT FORMAT`/`SAFETY REQUIREMENTS`) are present and ordered;
  imperative constraint language is present; equipment/day-count/disclaimer
  behavior is conditionally correct.
- **Groq client** — mocked success, authentication failure, connection error,
  timeout, rate limit, empty response, malformed response shape, and the
  retry-without-`reasoning_effort` fallback for models that reject it.
- **Service orchestration** — invalid input never reaches Groq; API failures and
  malformed/empty responses surface friendly errors; valid input returns a
  successful plan. The malformed-response check itself is a lightweight
  heuristic (looks for a `Day 1` heading), not a full Markdown parser — enough
  for this assignment's scope.

## 12. Prompt-Engineering Approach

`src/prompt_builder.py` builds a sectioned prompt from the structured
`WorkoutRequest` — it never concatenates inputs into a single sentence. Sections,
in order: `ROLE`, `USER PROFILE`, `CONSTRAINTS`, `WORKOUT DESIGN REQUIREMENTS`,
`OUTPUT FORMAT`, `SAFETY REQUIREMENTS`.

Key design choices:

- **Imperative constraint language** ("You MUST", "Do NOT invent equipment") in
  its own `CONSTRAINTS` section, rather than hoping the model infers limits from
  descriptive text.
- **Exact day-count enforcement** — the prompt states the required day count
  twice (constraints + output format) and asks for exactly that many `Day N`
  sections.
- **Equipment-scoped exercise selection** — the exact equipment list is stated
  and the model is explicitly told not to invent anything beyond it.
- **Conditional safety block** — a disclaimer is only requested when
  `limitations` is non-empty; when there are no limitations, the prompt
  explicitly tells the model *not* to add one, avoiding boilerplate noise.
- **Experience- and goal-scaled guidance** — separate guidance strings per
  experience level and per fitness goal (see `_EXPERIENCE_GUIDANCE` and
  `_GOAL_GUIDANCE` in `src/prompt_builder.py`) so a beginner/muscle-building
  prompt and an advanced/endurance prompt genuinely differ, not just in the
  numbers substituted in.
- **Structured Markdown output contract** — an explicit template (weekly
  overview, per-day warm-up + exercise/sets/reps/rest table, rest/recovery
  guidance, conditional safety note) so the response renders cleanly in
  Streamlit and isn't a wall of prose.

Iteration workflow and three representative test profiles (beginner/muscle/
3-day/dumbbells, intermediate/fat-loss/5-day/full-gym/bad-knees, beginner/
general/2-day/no-equipment/no-overhead-pressing) are documented in
`.claude/skills/prompt-design/SKILL.md`. Prompt *construction* is fully covered
by `tests/test_prompt_builder.py` without needing an API key. Actual **model
compliance** was also verified live against all three profiles: correct day
counts, no invented equipment, injury/limitation exclusions honored, and the
safety disclaimer appearing only when a limitation was provided. That pass
also surfaced and fixed two real issues in `src/groq_client.py` — a reasoning
model spending most of its token budget on hidden chain-of-thought and
truncating longer plans before the disclaimer, and the prompt occasionally
leaving a placeholder "Safety Note" heading when none was needed.

## 13. Stretch Goals Implemented

- [x] Regenerate button (re-invokes generation with the same inputs)
- [x] Last plan persisted in `st.session_state` across reruns
- [x] Download plan as `.md`
- [ ] "Swap this exercise" — intentionally skipped; the assignment calls this the
      lowest-priority stretch goal, and it would require structured/parseable
      per-exercise output disproportionate to its value for this assignment.

## 14. Assignment Rubric Checklist

| Criteria | Weight | Status |
|---|---|---|
| App runs without crashing on empty/invalid input | 20% | ✅ Validation gates the pipeline; 0/8 days, missing fields, and API/response failures all render friendly `st.error` messages. |
| Inputs are structured and correctly passed into the prompt | 25% | ✅ Five structured widgets → typed `WorkoutRequest` → every field appears in the prompt (tested). |
| Prompt design respects constraints, is well-structured, genuinely usable | 30% | ✅ Sectioned, imperative, constraint-explicit prompt (see Section 12); verified both by unit tests and live runs against Groq across the three profiles in `.claude/skills/prompt-design/SKILL.md` (correct day counts, equipment respected, injury exclusions honored, disclaimer only when needed). |
| Error handling (API failure, empty/malformed response) | 15% | ✅ Auth failure, connection error, timeout, rate limit, empty response, and malformed response are each handled distinctly and tested. |
| Code quality (type hints, function separation, readability) | 10% | ✅ Type hints throughout `app.py`/`src/`; UI, validation, prompt-building, and API access are separate modules; small single-purpose functions. |
