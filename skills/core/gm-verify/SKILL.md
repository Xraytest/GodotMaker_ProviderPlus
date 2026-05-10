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

**Permission:** Read-only with three exceptions — you may write `.godotmaker/current_role`, append to `.godotmaker/stage.jsonl`, and write `.godotmaker/verify_report.json`. Verify never modifies game code or planning docs.

## Resume Check

Read `.godotmaker/stage.jsonl` (treat as empty if missing) — each line is `{"role": X, "ts": Y}`.

- If **no event with `role == "build"` AND no event with `role == "fixgap"`** exists anywhere in the file → STOP. Tell user to run `/gm-build` first.
- If the **last event** has `role == "verify"` → STOP. Tell the user:
  > "Verify already ran at {timestamp} with no state-changing event since. Recommended next: /gm-evaluate.
  > If you need to redo this step or have other plans, just tell me."
- Otherwise → proceed (verify is naturally re-invoked after each build/fixgap cycle).

## Resolve `godot` binary

Read `godot_path` from `.claude/godotmaker.yaml` and substitute it
verbatim for `<godot_path>` in every `godot --headless …` command
below. The path was validated at publish time and is the source of
truth for which Godot binary this project uses.

If `.claude/godotmaker.yaml` is missing the `godot_path` field, fall
back to plain `godot` (PATH lookup). If THAT also fails, STOP and tell
the user `Godot binary not configured — re-run tools/publish.py to set
godot_path in .claude/godotmaker.yaml`. Do NOT spelunk through PATH
directories or guess install locations.

## Verification Checklist

Run each check in order. Record exact command and output.

### 1. Build
```bash
"<godot_path>" --headless --quit 2>&1
```
Criteria: zero ERROR lines in output.

### 2. Unit Tests
```bash
"<godot_path>" --headless --path . -s addons/gdUnit4/bin/GdUnitCmdTool.gd --ignoreHeadlessMode --add test/
```
Criteria: all tests pass (N passed, 0 failed). Note the path is `gdUnit4` (capital U) and the entry is `GdUnitCmdTool.gd`; `--ignoreHeadlessMode` is required for gdUnit4 v4.x to run under `--headless`.

### 3. Lint
**Currently disabled.** `gdtoolkit` (gdlint + gdformat) is not invoked
during verify. Reason: repeated
`gdtoolkit/linter/class_checks.py:144 NotImplementedError` crashes on
common ECS-style GDScript class shapes, plus low signal-to-noise versus
the headless compile (Section 1) and reviewer pattern checks (run during
gm-build's review pass). Re-enabling tracked as ROADMAP `R-112`.

Still write the `lint` block in `verify_report.json` (Section B) — set
`result: "pass"`, `issues: []`, `format_drift: null`. The schema requires
the field; an all-pass record is the no-op that lets consumers continue
to work without special-casing the disable.

### 4. Static Check
```bash
python tools/check_project.py <project_dir> --build --ecs --tests --plan --mcp
```
Criteria: no FAIL lines.

**Why not `--all`:** `--all` adds `--e2e`, which is the Evaluator's territory — verify must not gate it.

## Output Format

You produce **two outputs**:

### A. Human-readable report (chat)

```
## Verification Report

### Build
Command: "<godot_path>" --headless --quit 2>&1
Result: PASS | FAIL
Output: {paste actual output}

### Unit Tests
Command: {exact command}
Result: PASS | FAIL
Output: {N passed, M failed}

### Lint
Status: SKIP (gdtoolkit disabled — see "3. Lint" above; ROADMAP R-112)

### Static Check
Command: python tools/check_project.py <dir> --build --ecs --tests --plan --mcp
Result: PASS | FAIL
Output: {paste PASS/FAIL lines}

### Overall: PASS | FAIL
```

### B. Machine-readable report (`.godotmaker/verify_report.json`)

Write this file every run (PASS or FAIL). `/gm-build` and `/gm-fixgap` read it on their next invocation to translate failures into pending tasks.

Schema:

```json
{
  "result": "pass | fail",
  "ts": "<UTC ISO 8601 timestamp, e.g. 2026-05-07T14:23:00Z>",
  "checks": {
    "build": {
      "result": "pass | fail | error",
      "errors": [
        {"file": "src/foo.gd", "line": 42, "message": "Identifier 'bar' not declared"}
      ]
    },
    "unit_tests": {
      "result": "pass | fail | error",
      "passed": 624,
      "failed": 0,
      "failures": [
        {"test": "test_player_input::test_jump", "message": "expected 10, got 0"}
      ]
    },
    "lint": {
      "result": "pass | warn | fail | error",
      "issues": [
        {"file": "src/foo.gd", "rule": "max-line-length", "message": "line too long"}
      ],
      "format_drift": {
        "file_count": 92,
        "command": "gdformat src/ test/ scenes/"
      }
    },
    "static_check": {
      "result": "pass | fail | error",
      "issues": [
        {"check": "missing_unit_test", "detail": "s_level_up_overlay has no test"}
      ]
    }
  },
  "tooling_notes": [
    {
      "tool": "gdlint",
      "crashed_on": "src/foo.gd",
      "error": "NotImplementedError at gdtoolkit/linter/class_checks.py:144",
      "suggested_fallback": "exclude_file",

      "narrowed_command": null,
      "rule_name": null,
      "check_name": null
    }
  ]
}
```

Field rules:

- **Top-level `result`** — `"pass"` iff every `checks.*.result` ∈ {`pass`, `warn`}. Any `fail` / `error` makes overall `fail`. `tooling_notes` alone never makes overall `fail` — the `error` it pairs with does.
- **`ts`** — UTC ISO 8601 at the moment you write the file. Consumers compare it against their own last-event timestamp for freshness.
- **All array fields are required** (possibly empty `[]`). Do not omit them.
- **Per-check `result`** — `pass` / `fail` are project-content. `warn` is lint-only style noise. `error` means the tool itself crashed and the project's actual state is unknown for this check; pair `error` with exactly one `tooling_notes` entry. Consumers fix `error` via config, NOT project code.
- **`format_drift`** — object when `gdformat --check` reports drift; `null` otherwise.
- **`suggested_fallback`** + matching operand — the producer fills the operand so the consumer can act deterministically:

  | `suggested_fallback` | Required operand |
  |---|---|
  | `exclude_file` | `crashed_on` (already required on every note) |
  | `scope_narrow` | `narrowed_command` (replacement command, e.g. `"gdlint src/"`) |
  | `add_gdlintrc_rule` | `rule_name` (e.g. `"class-name"`) |
  | `skip_check` | `check_name` (e.g. `"missing_unit_test"`) |
  | `escalate` | — (none) |

  **Producer rule:** if you cannot fill the required operand for a non-`escalate` fallback, emit `escalate` instead.

  **Consumer rule** (open-enum forward-compat): a missing required operand or an unknown `suggested_fallback` value MUST be treated as `escalate` (surface to user, do NOT auto-fix). Never crash.

## On Failure

If any check fails:

1. Write `.godotmaker/verify_report.json` with `result: "fail"` and the per-check details.
2. Tell the user which checks failed. Suggest `/gm-build` if the last state-changing event was `build`, `/gm-fixgap` if it was `fixgap`.
3. Do NOT append a `verify` event to `stage.jsonl` — only PASS records a stage event.

## When Done

When all checks pass:

1. Write `.godotmaker/verify_report.json` with `result: "pass"` (Field rules apply: `tooling_notes == []`, all `checks.*.result` ∈ {`pass`, `warn`}).
2. From the project root run `python tools/append_stage_event.py verify` to append a `{"role": "verify", "ts": "<server-generated UTC>"}` line to `.godotmaker/stage.jsonl`. Do NOT hand-write the JSON or the timestamp — the helper exists so the timestamp comes from the system clock, not your own output.
3. Inform the user: `Verify complete. Recommended next: /gm-evaluate`
