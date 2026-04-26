---
name: gm-build
description: |
  Implement game systems via worker dispatch. Covers Stage 5 (Risk) and Stage 6 (Main).
  Dispatches workers continuously, triggers verification every ≥5 completed workers.
  Explicit invocation only — use /gm-build.
disable-model-invocation: true
---

# GodotMaker Build

$ARGUMENTS

You are implementing a Godot game by dispatching Worker subagents. This covers Stage 5 (Risk Implementation) and Stage 6 (Main Implementation).

## Session Setup

**FIRST ACTION — before anything else:** Write `build` to `.godotmaker/current_role`.

## Resume Check

Read `.godotmaker/stage.jsonl` (treat as empty if missing) — each line is `{"role": X, "ts": Y}`. Build the set of completed roles from these events.

- If `setup` has not completed → STOP. Tell user to run `/gm-setup` first.
- If `build` has already completed AND all PLAN.md tasks are `verified` → STOP. Tell the user:
  > "Role 'build' was already completed at {timestamp}. Recommended next: /gm-verify.
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

### Step 1 — Dispatch Workers

- Read `.claude/skills/orchestrator/worker-dispatch.md` for the brief template
- Use `subagent_type: "worker"`. Each worker implements ONE system + its unit tests.
- Max 3 in parallel with disjoint file sets via `isolation: "worktree"` (send all Agent calls in one message).
- After each worker reports DONE, mark its task in PLAN.md as `completed`.

### Step 2 — Trigger Verification Round (every ≥5 completed workers)

Once 5 or more workers have completed since the last verification round:

**Verifier:**
- Read `.claude/skills/orchestrator/verifier-dispatch.md` for the brief template
- Use `subagent_type: "verifier"`. Pass each worker's deliverables since the last round.
- On FAIL: add a NEW pending task in PLAN.md to fix it. The failed task stays `completed`.
- On PASS: update those tasks from `completed` → `verified`.

**Reviewer** (after verifier passes):
- Read `.claude/skills/orchestrator/reviewer-dispatch.md` for the brief template
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

**In your context:** PLAN.md status, STRUCTURE.md architecture, worker briefs (~200 tokens), worker summaries (~100 tokens), verification results, design decisions.

**Out of your context (delegate to workers):** Asset generation, system implementation code, test code, build/lint output, screenshot analysis.

**When context gets large:** Summarize completed phases. Reference documents by path. Write decisions to MEMORY.md for recovery after compaction.

## When Done

When ALL PLAN.md tasks are `verified` AND the most recent verification round produced no new fix tasks:

1. Append a line to `.godotmaker/stage.jsonl`: `{"role": "build", "ts": "<UTC ISO timestamp>"}`. Read the existing file (treat as empty if missing), append the new event, and write the full file back.
2. Inform the user: `Build complete. Recommended next: /gm-verify`