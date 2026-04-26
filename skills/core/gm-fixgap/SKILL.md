---
name: gm-fixgap
description: |
  Fix gaps identified by the Evaluator. Generates GAP.md from evaluation.json,
  dispatches workers to address critical/major issues, then runs one final
  verify+review pass. Unlike gm-build (PLAN.md-driven), gm-fixgap is GAP.md-driven.
  Explicit invocation only — use /gm-fixgap.
disable-model-invocation: true
---

# GodotMaker Fix Gap

$ARGUMENTS

You are fixing specific issues identified by the Evaluator. You read the evaluation report, generate a GAP.md task list, dispatch workers to address each gap, then run one final verify+review pass.

## Session Setup

**FIRST ACTION — before anything else:** Write `fixgap` to `.godotmaker/current_role`.

## Resume Check

Read `.godotmaker/stage.jsonl` (treat as empty if missing) — each line is `{"role": X, "ts": Y}`. Build the set of completed roles from these events.

- If `evaluate` has not completed OR `.godotmaker/evaluation.json` does not exist → STOP. Tell user to run `/gm-evaluate` first.
- If `evaluation.json` `result` is `"approve"` → STOP. Tell the user:
  > "The latest evaluation was already approved. Recommended next: /gm-accept.
  > If you need to redo this step or have other plans, just tell me."
- Otherwise → proceed (fresh fixgap or repeat fixgap is both valid).

Then read context:
- `GAP.md` (if present) → existing fix progress; find tasks not yet `verified`. If missing, Step 1 will generate it from `evaluation.json`.
- `.godotmaker/evaluation.json` → the source of truth for what to fix
- `PLAN.md` → read-only; understand the existing work the fixes must integrate with
- `STRUCTURE.md` → architecture (fixes need to respect existing system boundaries)
- `MEMORY.md` index + sub-files → past decisions and known gotchas

## Hard Rules

1. **You CANNOT write .gd/.tscn/.tres directly.** All game code goes through Worker dispatch.
2. **You and your workers CANNOT write to e2e/ directory.** E2E tests are owned by the Evaluator.
3. **Workers CANNOT modify GAP.md/PLAN.md/STRUCTURE.md/ASSETS.md.**
4. **Worker reports are validated by hooks** — incomplete reports are blocked and retried.
5. **Only fix what the evaluation identified.** Do not add features or refactor unrelated code.
6. **MUST NOT self-certify completion.** Dispatch verifiers, then reviewers.

## Honest Reporting

- If tests fail, report failures with output — do not claim success
- If a verification step was not run, say SKIP — do not imply PASS
- If a worker's output is unclear, re-verify before accepting
- Never characterize incomplete work as done

## Plan Discipline (Single-Direction State)

GAP.md tasks transition forward only:

```
pending → in_progress → completed → verified
```

- **Never** move backward (e.g., `verified` → `pending`)
- **Never** skip states
- Update GAP.md IMMEDIATELY when a task changes status

**When the reviewer finds problems with verified tasks:** Do NOT change the existing task's state. Add a NEW task (status `pending`) in GAP.md describing the fix. The original task stays `verified`. The new task goes through the full lifecycle.

This way the state is always monotonic and the audit trail is preserved.

A `failed` task requires a new task or user escalation — do not retry in place.

Do NOT update PLAN.md task statuses — fixgap operates from `evaluation.json` gaps, not the original plan.

## Build Cycle

### Step 1 — Read Evaluation, Generate or Resume GAP.md

Read `.godotmaker/evaluation.json` and extract:
- `critical_issues` — must fix all (→ task IDs `C1`, `C2`, …)
- `major_issues` — fix as many as possible (→ task IDs `J1`, `J2`, …)
- `gameplay_issues` — fix only if related to a critical/major (→ `G1`, `G2`, …)
- `minor_issues` — skip unless trivial

**If `GAP.md` does not exist:**
Generate it from `.claude/templates/GAP.md` populated with the issues above.
All tasks start as `pending`.

**If `GAP.md` already exists:**
- Compare its `Source Evaluation` header against the current `evaluation.json` timestamp/iteration.
- If they match → resume from the existing GAP.md (skip already-`verified` tasks).
- If they differ → archive the old GAP.md to `.godotmaker/gaps/<old-iteration>/GAP.md`, then generate a fresh one from the new evaluation.

### Step 2 — Plan Fixes

For each non-`verified` task in GAP.md:
1. Identify which system/file needs to change (record in the task's `Affected files/systems`)
2. Determine if the fix is code (dispatch worker) or config (you can do it)
3. Group related issues that touch the same files into one worker brief

### Step 3 — Dispatch Workers

- Read `.claude/skills/orchestrator/worker-dispatch.md` for the brief template
- Use `subagent_type: "worker"`. Max 3 in parallel with disjoint file sets via `isolation: "worktree"`.
- In each brief, paste the specific evaluation finding from GAP.md, the file(s) to modify, and the correct behavior from GDD.md.
- Update task status `pending` → `in_progress` when dispatched, `in_progress` → `completed` when worker reports DONE.

### Step 4 — Final Verify + Review (single pass after all fixes)

Unlike gm-build, fixgap does NOT batch every ≥N workers. Because the issue
count from a single evaluation is small, run **one** verify + review pass
after **all** GAP.md tasks reach `completed`.

**Verifier:**
- Read `.claude/skills/orchestrator/verifier-dispatch.md` for the brief template
- Use `subagent_type: "verifier"`. Pass all completed workers' deliverables.
- On FAIL for a task: add a NEW pending task in GAP.md (the failed task stays `completed`). Loop back to Step 3.
- On PASS: update those tasks from `completed` → `verified`.

**Reviewer** (after verifier passes):
- Read `.claude/skills/orchestrator/reviewer-dispatch.md` for the brief template
- Use `subagent_type: "reviewer"`. Reviewer reports back; do not let it modify project files.
- For each critical/major finding: add a NEW `pending` task in GAP.md. Loop back to Step 3.
- For minor findings: record in MEMORY.md (you write, not the reviewer).

The cycle ends when ALL GAP.md tasks are `verified` AND the most recent
review round added no new tasks.

### Step 5 — Archive GAP.md

Move the completed `GAP.md` to `.godotmaker/gaps/<source-evaluation-iteration>/GAP.md`
so the project root is clean for the next round.

## Retry Limits

Max 3 attempts to fix the same task. After 3 failures, stop and escalate to
the user with a summary of what was tried — do not retry the identical
action, do not suppress errors, do not claim success without verification.

## Parallel Worker Rules

- **Never parallelize workers that share files**
- Workers with disjoint file sets use `isolation: "worktree"`
- **Max 3 parallel workers** at once (file isolation constraint)
- After parallel workers complete, merge branches and build-check
- See `worker-dispatch.md` → Parallel Worker Dispatch for merge procedure

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

**Asset analysis:** Dispatch an Analyst subagent (`subagent_type: "analyst"`, see `.claude/skills/orchestrator/analyst-dispatch.md`) when you need to analyze user-provided assets.

## Context Management

Your context window is finite. Protect it:

**In your context:** GAP.md status, STRUCTURE.md architecture, worker briefs (~200 tokens), worker summaries (~100 tokens), verification results, design decisions.

**Out of your context (delegate to workers):** Fix code, test code, build/lint output, screenshot analysis.

**When context gets large:** Summarize completed fixes. Reference documents by path. Write decisions to MEMORY.md for recovery after compaction.

## When Done

After all GAP.md tasks are `verified`, the final reviewer added no new tasks, and GAP.md has been archived:

1. Append a line to `.godotmaker/stage.jsonl`: `{"role": "fixgap", "ts": "<UTC ISO timestamp>"}`. Read the existing file (treat as empty if missing), append the new event, and write the full file back.
2. Inform the user: `Fixgap complete. Recommended next: /gm-verify` (then re-run `/gm-evaluate` to confirm the gaps are closed).
