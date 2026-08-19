# Prompt Engineering Rules

This is the most important rule file in the project — the assignment is graded 30%
on prompt design. `src/prompt_builder.py` builds the prompt; it is reviewed against
this checklist by `.claude/agents/prompt-reviewer.md`.

## The prompt must

1. Clearly define the LLM's role (e.g. "You are an experienced, safety-conscious
   personal trainer...") at the top of the prompt.
2. Include, from the structured `WorkoutRequest`:
   - fitness goal
   - experience level
   - available days per week
   - equipment access
   - injuries/limitations (if provided)
3. Explicitly instruct the model to respect all constraints — imperative language
   ("You MUST design around the equipment listed below"), not passive/hopeful
   phrasing.
4. Explicitly prohibit exercises that conflict with stated limitations, using the
   user's own limitation text, not a generic warning.
5. Produce a structured weekly plan, not a wall of prose.
6. Require, per training day: day label, focus/muscle group, exercises, sets, reps,
   rest.
7. Adjust complexity based on experience level (beginner = fundamental movements and
   more guidance; advanced = higher complexity/intensity, less hand-holding).
8. Adjust exercise selection based on equipment access — only exercises performable
   with the exact equipment listed.
9. Adjust weekly structure based on number of available days — exactly that many
   training days, with rest/recovery guidance for the remainder of the week.
10. Avoid generic responses ("do some squats") — the prompt must push toward
    specificity tied to the user's actual profile.
11. Avoid medical diagnosis or medical claims of any kind.
12. If injuries/limitations are provided, instruct the model to include a concise
    safety disclaimer in the output. If no limitations are provided, do not request
    an injury disclaimer.
13. Never invent equipment the user does not have.
14. Never silently ignore a user constraint — if a constraint cannot be fully
    satisfied, the model should say so rather than drop it silently (this instruction
    itself belongs in the prompt).

## Required prompt sections

The prompt must be organized into these clearly labeled sections, in this order:

```
ROLE
USER PROFILE
CONSTRAINTS
WORKOUT DESIGN REQUIREMENTS
OUTPUT FORMAT
SAFETY REQUIREMENTS
```

## Anti-patterns to avoid

- Concatenating inputs into a single natural-language sentence and hoping the model
  infers the constraints.
- Vague instructions like "keep it safe" instead of specific, itemized rules.
- Requesting free-form prose output instead of a specified Markdown structure.
- Applying the same disclaimer/safety text regardless of whether limitations were
  provided.
- Hardcoding example exercises into the prompt that bias every response toward the
  same plan regardless of profile.

See `.claude/skills/prompt-design/SKILL.md` for the iterative workflow and test
profiles used to validate the prompt, and `.claude/agents/prompt-reviewer.md` for the
review checklist.
