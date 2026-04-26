---
name: gm-accept
description: |
  Present final results to the user for acceptance.
  Shows evaluation results, evaluator screenshots, and asks for confirmation.
  Explicit invocation only — use /gm-accept.
disable-model-invocation: true
---

# GodotMaker Accept

$ARGUMENTS

You are presenting the completed game to the user for acceptance.

## Session Setup

**FIRST ACTION — before anything else:** Write `accept` to `.godotmaker/current_role`.

## Resume Check

Read `.godotmaker/stage.jsonl` (treat as empty if missing) — each line is `{"role": X, "ts": Y}`. Build the set of completed roles from these events. Also read `.godotmaker/evaluation.json`.

- If `evaluate` has not completed OR `evaluation.json` does not exist → STOP. Tell user to run `/gm-evaluate` first.
- If `evaluation.json` `result` is `"reject"` → STOP. Tell user to run `/gm-fixgap` first.
- If `accept` has already completed → STOP. Tell the user:
  > "Role 'accept' was already completed at {timestamp}. Recommended next: /gm-finalize.
  > If you need to redo this step or have other plans, just tell me."
- Otherwise → proceed.

## Process

### 1. Gather Results

Read these files:
- `.godotmaker/evaluation.json` — evaluator results (mandatory)
- `PLAN.md` — task completion status
- `MEMORY.md` — known issues and discoveries
- `GDD.md` — original requirements

### 2. Collect Screenshots

Do NOT capture new screenshots. Use the screenshots already captured by the Evaluator:
- Look in `e2e/screenshots/` for `scene_{name}.png` files
- These correspond to reference images in `references/scene_{name}.png`
- If no evaluator screenshots exist, note this as a gap

### 3. Present to User

Format a clear summary:

```
## Game Summary

**Project:** {name}
**Description:** {from GDD}

### What Was Built
- {N} systems, {M} components
- {key features list}

### Test Results
- Unit tests: {from gm-verify results or PLAN.md}
- E2E tests: {from evaluation.json e2e_tests}

### Evaluation Result: APPROVED
- Mandatory checks: all passed
- Visual checks: {summary}
- Gameplay issues: {from evaluation.json, or "none"}

### Known Limitations
- {from MEMORY.md and evaluation minor_issues}

### How to Run
{instructions}

### Screenshots
{show evaluator screenshots side-by-side with references}
```

### 4. Ask for Decision

Use AskUserQuestion to ask:
- **Accept** → I'll record acceptance and recommend /gm-finalize.
- **Fix issues** → tell me what to fix and I'll dispatch /gm-fixgap.
- **Done for now** → progress is saved; you can resume any time."

Do NOT proceed until the user replies. Their reply drives the When Done branch below.

## When Done

Always append a trace event to `.godotmaker/stage.jsonl` recording the user's decision, regardless of which branch was chosen:

```
{"role": "accept", "ts": "<UTC ISO timestamp>", "decision": "<accept|fix|done>"}
```

(Read the existing file, append the new event, write the full file back.)

Then, based on the decision:
- **accept** → Inform the user: `Accepted. Recommended next: /gm-finalize`
- **fix** → Inform the user to run `/gm-fixgap` with specific fix instructions
- **done** → Inform the user: `Progress saved; resume any time`

Note: only events with `decision == "accept"` count as the role having truly completed for `/gm-finalize`'s prerequisite check. The `fix` and `done` events are kept as audit trail.
