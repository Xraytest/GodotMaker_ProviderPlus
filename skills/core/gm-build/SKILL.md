---
name: gm-build
description: |
  Implement game systems via worker dispatch. Covers risk-first then main implementation.
  Dispatches workers continuously, triggers verification every ≥5 completed workers.
  Explicit invocation only — use /gm-build.
disable-model-invocation: true
---

# GodotMaker Build

$ARGUMENTS

You are implementing a Godot game by dispatching Worker subagents. Risk tasks first, then main tasks — both surfaced from PLAN.md.

## Session Setup

**FIRST ACTION — before anything else:** Write `build` to `.godotmaker/current_role`.

## Resume Check

Read `.godotmaker/stage.jsonl` (treat as empty if missing) — each line is `{"role": X, "ts": Y}`.

- If `project.godot` does not exist → STOP. Tell user to run `/gm-scaffold` first.
- If **no event with `role == "gdd"`** exists anywhere in the file → STOP. Tell user to run `/gm-gdd` first.
- If the **last event** has `role == "build"` AND all PLAN.md tasks are `verified` → STOP. Tell the user:
  > "Build already completed for this milestone at {timestamp}. Recommended next: /gm-verify.
  > If you need to redo this step or have other plans, just tell me."
- Otherwise → proceed (this includes resume from interrupted run AND new tasks added by reviewer).

Then read context:
- `PLAN.md` → find pending/in_progress/completed tasks (anything not `verified`)
- `STRUCTURE.md` → architecture and build order
- `MEMORY.md` index + sub-files → avoid repeating known mistakes

## Hard Rules

1. **You CANNOT write .gd/.tscn/.tres directly.** All game code goes through Worker dispatch.
2. **You and your workers CANNOT write to e2e/ directory.** E2E tests are owned by the Evaluator.
3. **Workers CANNOT modify PLAN.md/STRUCTURE.md/ASSETS.md.**
4. **Worker reports are validated by hooks** — incomplete reports are blocked and retried.
5. **MUST NOT skip stages.** Fix issues first; report to user after 3 attempts.
6. **MUST NOT self-certify completion.** Dispatch verifiers, then reviewers.

## Honest Reporting

- If tests fail, report failures with output — do not claim success
- If a verification step was not run, say SKIP — do not imply PASS
- If a worker's output is unclear, re-verify before accepting
- Never characterize incomplete work as done

## Plan Discipline (Single-Direction State)

Tasks transition forward only:

```
pending → in_progress → completed → verified
```

- **Never** move backward (e.g., `verified` → `pending`)
- **Never** skip states
- Update PLAN.md IMMEDIATELY when a task changes status

**When the reviewer finds problems with verified tasks:** Do NOT change the existing task's state. Add a NEW task (status `pending`) describing the fix. The original task stays `verified`. The new task goes through the full lifecycle.

This way the state is always monotonic and the audit trail is preserved.

A `failed` task requires a new task or user escalation — do not retry in place.

## Build Cycle

Track a running count of workers completed since the last verification round.

### Step 0 — Process Verify Feedback

Run this step before Step 1 only if `.godotmaker/verify_report.json` exists, `result == "fail"`, and its `ts` is later than the most recent `role == "build"` event in `stage.jsonl` (or there is no prior build event). Otherwise → skip to Step 1.

Translate failures into `pending` tasks at the bottom of `PLAN.md`.

**Project-code tasks** (any `checks.<name>.result == "fail"`) — go through the normal Worker → Verifier → Reviewer cycle:

- `checks.build.errors[]` → one task per distinct compile error (file + line + message in Notes).
- `checks.unit_tests.failures[]` → one task per failing test. If `failed > 0` but `failures[]` is empty, one task: "investigate test runner output".
- `checks.lint.issues[]` → group by file when multiple issues hit the same file; otherwise one per issue.
- `checks.lint.format_drift` → one task: "run `<format_drift.command>` to format the drifted files (`<file_count>` files)".
- `checks.static_check.issues[]` → one task per issue, using `check` as the title prefix (e.g. `missing_unit_test: s_player_input`). For unknown `check` discriminators, use the raw value verbatim — generic project-code fix.

**Config tasks** (any `checks.<name>.result == "error"`, paired with one `tooling_notes[]` entry) — main agent applies directly, NO worker dispatch:

- Routable fallback (`exclude_file` / `scope_narrow` / `add_gdlintrc_rule` / `skip_check`) WITH operand present (per the fallback table in `gm-verify/SKILL.md` Section B) → apply the structured edit using the note's operand. Mark `verified` after the next verify round confirms the tool no longer crashes there. Hard Rule 1 only restricts `.gd/.tscn/.tres`.
- `escalate`, OR routable with missing operand, OR unknown discriminator → do NOT auto-fix. Surface `tool` + `error` + `crashed_on` (and any original `suggested_fallback`) to the user verbatim, halt the build cycle, leave the task `pending` until the user resolves the underlying issue.

Do NOT delete project code as a "fix" for a tool crash.

### Step 1 — Dispatch Workers

- Read `references/worker-dispatch.md` for the brief template
- Use `subagent_type: "worker"`. Each worker implements ONE system + its unit tests.
- Max 3 in parallel with disjoint file sets via `isolation: "worktree"` (send all Agent calls in one message).
- After each worker reports DONE, mark its task in PLAN.md as `completed`.

### Step 2 — Trigger Verification Round (every ≥5 completed workers)

Once 5 or more workers have completed since the last verification round:

**Verifier:**
- Read `references/verifier-dispatch.md` for the brief template
- Use `subagent_type: "verifier"`. Pass each worker's deliverables since the last round.
- On FAIL: add a NEW pending task in PLAN.md to fix it. The failed task stays `completed`.
- On PASS: update those tasks from `completed` → `verified`.

**Reviewer** (after verifier passes):
- Read `references/reviewer-dispatch.md` for the brief template
- Use `subagent_type: "reviewer"`. Reviewer reports back; do not let it modify project files.
- For each critical/major finding: add a NEW pending task in PLAN.md.
- For minor findings: record in MEMORY.md (you write, not the reviewer).

Reset the worker counter after this round. Continue dispatching (which now includes the new fix tasks).

### Step 3 — Final Verification Round

After ALL tasks are `verified` (PLAN.md has no `pending`/`in_progress`/`completed`), if any workers completed since the last verification round, run one final verifier + reviewer to cover the remainder.

If the final reviewer adds new tasks, go back to Step 1. The build cycle continues until ALL tasks are `verified` AND the most recent verification round produced no new tasks.

## Retry Limits

Max 3 attempts to fix the same task. After 3 failures, stop and escalate to
the user with a summary of what was tried — do not retry the identical
action, do not suppress errors, do not claim success without verification.

## Parallel Worker Rules

- **Never parallelize workers that share files**
- Workers with disjoint file sets use `isolation: "worktree"`
- **Max 3 parallel workers** at once (file isolation constraint)
- After parallel workers complete, merge branches and build-check
- See `references/worker-dispatch.md` → Parallel Worker Dispatch for merge procedure

## Memory System

```
MEMORY.md              <- Index + cross-cutting knowledge
memory/
  {system_name}.md     <- Per-system details (template: .claude/templates/memory_subsystem.md)
```

- Read MEMORY.md before dispatching workers
- Update after every verification round (you write, not workers/reviewers)

## Available Skills & Tools

| Skill | Purpose | Path |
|-------|---------|------|
| gecs | ECS framework API + patterns | .claude/skills/gecs/SKILL.md |
| headless-build | Compile verification | .claude/skills/headless-build/SKILL.md |
| gdunit-driver | Unit test execution | .claude/skills/gdunit-driver/SKILL.md |
| gdtoolkit | GDScript lint + format | .claude/skills/gdtoolkit/SKILL.md |
| godot-api | Godot API reference | .claude/skills/godot-api/SKILL.md |
| screenshot | Gameplay screenshot capture | .claude/skills/screenshot/SKILL.md |
| mcp-driver | Runtime debugging via godot-mcp | .claude/skills/mcp-driver/SKILL.md |

**Asset analysis:** Dispatch an Analyst subagent (`subagent_type: "analyst"`, see `references/analyst-dispatch.md`) when you need to analyze user-provided assets.

## Context Management

Your context window is finite. Protect it:

**In your context:** PLAN.md status, STRUCTURE.md architecture, worker briefs (~200 tokens), worker summaries (~100 tokens), verification results, design decisions.

**Out of your context (delegate to workers):** Asset generation, system implementation code, test code, build/lint output, screenshot analysis.

**When context gets large:** Summarize completed phases. Reference documents by path. Write decisions to MEMORY.md for recovery after compaction.

## When Done

When ALL PLAN.md tasks are `verified` AND the most recent verification round produced no new fix tasks:

1. Append a line to `.godotmaker/stage.jsonl`: `{"role": "build", "ts": "<UTC ISO timestamp>"}`. Read the existing file (treat as empty if missing), append the new event, and write the full file back.
2. Inform the user: `Build complete. Recommended next: /gm-verify`