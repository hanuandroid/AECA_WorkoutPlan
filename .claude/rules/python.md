# Python Rules

- Every function has type hints on all parameters and its return type — no bare
  `def foo(x):`.
- Use descriptive names for functions, variables, and parameters over abbreviations
  (`fitness_goal`, not `fg`).
- Keep functions small and focused on a single responsibility; if a function is
  doing validation *and* formatting *and* I/O, split it.
- Every function has a clear, explicit return type — avoid implicit `None`-or-value
  returns; prefer a typed result object (see `src/models.py`) over ad-hoc tuples or
  dicts for anything crossing a module boundary.
- Avoid duplicated logic — if the same check or transformation appears twice, extract
  it.
- Use `dataclass` (or another typed model) for structured data that flows between
  modules (`WorkoutRequest`, `ValidationResult`, `ServiceResult`) instead of passing
  loose dicts or positional args.
- Use meaningful, specific exception handling — catch the exception types you
  actually expect and know how to handle; never a bare `except:`.
- Use module-level constants for fixed configuration (allowed dropdown values, model
  name, timeout values) instead of inline string/number literals scattered through
  the code.
- Keep UI code (Streamlit widgets, page layout) out of `src/` — `src/` modules must
  be importable and testable without Streamlit running.
