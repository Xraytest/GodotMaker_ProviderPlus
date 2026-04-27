---
name: gm-verify
description: |
  Mechanical verification of the built game: headless build, unit tests, lint, static checks.
  Explicit invocation only — use /gm-verify.
disable-model-invocation: true
---

# GodotMaker Verify

$ARGUMENTS

You are performing mechanical verification of a built Godot game project. This is a non-creative, checklist-driven process.

## Session Setup

**FIRST ACTION — before anything else:** Write `verify` to `.godotmaker/current_role`.

## Resume Check

Read `.godotmaker/stage.jsonl` (treat as empty if missing) — each line is `{"role": X, "ts": Y}`.

- If **no event with `role == "build"` AND no event with `role == "fixgap"`** exists anywhere in the file → STOP. Tell user to run `/gm-build` first.
- If the **last event** has `role == "verify"` → STOP. Tell the user:
  > "Verify already ran at {timestamp} with no state-changing event since. Recommended next: /gm-evaluate.
  > If you need to redo this step or have other plans, just tell me."
- Otherwise → proceed (verify is naturally re-invoked after each build/fixgap cycle).

## Verification Checklist

Run each check in order. Record exact command and output.

### 1. Build
```bash
godot --headless --quit 2>&1
```
Criteria: zero ERROR lines in output.

### 2. Unit Tests
```bash
godot --headless -s addons/gdunit4/bin/gdunit4_run.gd
```
Criteria: all tests pass (N passed, 0 failed).

### 3. Lint
```bash
gdlint .
gdformat --check .
```
Criteria: no errors (warnings acceptable).

### 4. Static Check
```bash
python tools/check_project.py <project_dir> --all
```
Criteria: no FAIL lines.

## Output Format

```
## Verification Report

### Build
Command: godot --headless --quit 2>&1
Result: PASS | FAIL
Output: {paste actual output}

### Unit Tests
Command: {exact command}
Result: PASS | FAIL
Output: {N passed, M failed}

### Lint
Command: gdlint .
Result: PASS | WARN | FAIL
Output: {summary}

### Static Check
Command: python tools/check_project.py <dir> --all
Result: PASS | FAIL
Output: {paste PASS/FAIL lines}

### Overall: PASS | FAIL
```

## On Failure

If any check fails:
1. Identify the failing system from the output
2. Tell the user which checks failed. Suggest the right next step based on context:
   - If the last state-changing event was `build` → suggest `/gm-build` (the build cycle continues)
   - If the last state-changing event was `fixgap` → suggest `/gm-fixgap` (the gap-fix cycle continues)

Do NOT dispatch workers or make code changes. Verify only reports — fixing happens in `/gm-build` or `/gm-fixgap`.

## When Done

When all checks pass:

1. Append a line to `.godotmaker/stage.jsonl`: `{"role": "verify", "ts": "<UTC ISO timestamp>"}`. Read the existing file (treat as empty if missing), append the new event, and write the full file back.
2. Inform the user: `Verify complete. Recommended next: /gm-evaluate`
