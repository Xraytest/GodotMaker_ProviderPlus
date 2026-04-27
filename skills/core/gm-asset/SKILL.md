---
name: gm-asset
description: |
  Asset collection + generation. Reads ASSETS.md MISSING entries, dispatches
  an analyst subagent for user-provided image inspection, calls
  tools/asset_gen.py (Bash) for AI generation, updates ASSETS.md status.
  Re-runnable any time during a milestone (user can add new art mid-development).
  Explicit invocation only — use /gm-asset.
disable-model-invocation: true
---

# GodotMaker Asset

$ARGUMENTS

You are filling in the missing assets identified in `ASSETS.md`. Image analysis runs in an analyst subagent (context isolation for image binaries); AI generation is a direct Bash call to `tools/asset_gen.py` — no worker subagent needed.

This skill is **per-milestone re-runnable**: a user can call `/gm-asset` between build batches when they add new art files. Each invocation processes whatever is currently `MISSING`.

## Session Setup

**FIRST ACTION — before anything else:** Write `asset` to `.godotmaker/current_role`.

## Resume Check

Asset is re-runnable per milestone, so the gate is the current state of `ASSETS.md`, not events in `stage.jsonl`.

- If `project.godot` does not exist → STOP. Tell user to run `/gm-scaffold` first.
- If `ASSETS.md` does not exist → STOP. Tell user to run `/gm-gdd` first.
- Read `ASSETS.md` Asset Table. If no rows have status `MISSING` (all are `provided`/`generated`/`N/A`) → STOP. Tell the user:
  > "No MISSING assets to process. Recommended next: /gm-build.
  > If you've added new art files since last run, just tell me and I'll re-scan."
- Otherwise → proceed.

## Hard Rules

1. **Direct Write/Edit by you (main agent) is restricted to project-root `ASSETS.md` and files under `.godotmaker/`.** Files in `assets/` and `references/` reach disk only via:
   - `tools/asset_gen.py` invoked through Bash (a subprocess — hook does not police its writes), OR
   - the analyst subagent (Step 2).
   You never write image files yourself. The hook boundary is your Write/Edit tool calls; Bash subprocesses fall outside it by design — this is the intended path for AI generation, not a loophole to abuse.
2. **Image analysis MUST go through the analyst subagent.** Do NOT Read image binaries from `assets/` yourself — they pollute context. Dispatch analyst when you need style/dimension/role extraction.
3. **You CANNOT modify PLAN.md, GAP.md, STRUCTURE.md, SCENES.md.** Asset work is isolated from gameplay planning. Code-art coupling issues surface in `/gm-evaluate` and are addressed in `/gm-fixgap` or the next milestone.
4. **You CANNOT write game code.** Code lives in `/gm-build` workers.
5. **Audio MUST be user-provided** — AI audio generation is not supported. Mark audio as deferred and remind the user.

## Process

### Step 1 — Inventory MISSING

Read `ASSETS.md` Asset Table. Build a list of MISSING items grouped by type:
- **Art (sprites, textures, references):** can be user-provided or AI-generated
- **Audio:** must be user-provided
- **Scene reference images:** AI-generated based on SCENES.md descriptions

### Step 2 — Collect User-Provided Files

Use `AskUserQuestion`:
> "I'm about to fill in {N} missing assets. Do you want to provide any of them yourself before I generate? Audio MUST be user-provided. Place files in `assets/` and tell me when ready."

If user provides files:

1. Wait for user confirmation that files are placed.
2. Dispatch an **analyst subagent** (`subagent_type: "analyst"`, see `.claude/skills/orchestrator/analyst-dispatch.md`) to inspect the files and generate/update `assets/manifest.json`.
   - **Do NOT read image files yourself.** All image analysis goes through the analyst.
   - Analyst extracts: type, role, dimensions, palette, style characteristics.
3. After analyst reports, update ASSETS.md: change matching `MISSING` rows to `provided` and record extracted style notes in Art Direction (if first user-provided batch).

### Step 3 — Generate Scene Reference Images (if MISSING)

For each scene in SCENES.md whose `references/scene_{name}.png` is missing:

1. Build the prompt from the scene's Elements + Mood (per `.claude/skills/orchestrator/asset-planner.md`):
   - Style anchors (if user provided art): reference the user asset files
   - Style fallback (if no user art): GDD §4 art direction + ASSETS.md Art Direction
2. Run via Bash:
   ```bash
   python tools/asset_gen.py --prompt "..." --output references/scene_{name}.png
   ```
3. Show the result to the user. If rejected, regenerate with adjusted prompt.

### Step 4 — Generate Remaining MISSING Art

For all remaining MISSING art assets in ASSETS.md (excluding audio):

Confirm with user:
> "I'll AI-generate the following: {list}. {if user art: 'Style will match your existing assets.'} OK to proceed?"

After confirmation, run `python tools/asset_gen.py` once per asset (per `asset-planner.md` + `asset-gen.md` for prompt construction). Sequential is fine — generation latency is API-bound, not CPU-bound. If you want concurrency, use `&` to background several Bash calls and `wait` for them.

### Step 5 — Update ASSETS.md

After all generation calls return:
- Change generated rows from `MISSING` → `generated` with file path + generation params
- Audio rows that user did not provide → mark `deferred` (with user acknowledgment)
- Verify total MISSING count is zero (or all remaining are deferred audio with user OK)

## Plan Discipline

ASSETS.md is the only document you may modify. Status transitions are forward-only:

```
MISSING → provided | generated | N/A | deferred
```

Never revert a `provided`/`generated` row back to `MISSING` — if the user wants to regenerate, treat it as a NEW row or note in MEMORY.md.

## Available Skills & Tools

**Skills:**
| Skill | Purpose |
|-------|---------|
| screenshot | Capture for visual cross-check |
| visual-qa | Style consistency check |

**CLI tools (call via Bash):**
| Tool | Purpose |
|------|---------|
| `tools/asset_gen.py` | AI image generation (Gemini) |

**Reference docs (read for prompt construction):**
- `.claude/skills/orchestrator/asset-planner.md` — generation brief template
- `.claude/skills/orchestrator/asset-gen.md` — `asset_gen.py` usage details

**Asset analysis:** Dispatch an Analyst subagent (`subagent_type: "analyst"`, see `.claude/skills/orchestrator/analyst-dispatch.md`).

## Context Management

Keep `ASSETS.md` state and the MISSING list in context. Delegate image binaries to the analyst subagent (do NOT Read images directly). Generation prompts can stay in context — they're cheap text.

## When Done

After ASSETS.md has no MISSING rows (or all remaining are deferred audio with user acknowledgment):

1. Append a line to `.godotmaker/stage.jsonl`: `{"role": "asset", "ts": "<UTC ISO timestamp>"}`. Read the existing file (treat as empty if missing), append the new event, and write the full file back.
   (The Resume Check above reads `ASSETS.md`, not this event — the stage.jsonl entry exists so `stage_reminder.py` can suggest `/gm-build` next.)
2. Inform the user: `Asset complete. Recommended next: /gm-build` (or re-invoke /gm-asset later if you add more art).
