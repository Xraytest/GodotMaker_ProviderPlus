---
name: gm-gdd
description: |
  Game Design Document phase for one tag. On the first ever run, runs the
  full Socratic interview, produces GDD.md, and derives ROADMAP.md (split
  into SemVer-tagged release tags). On every subsequent run, focuses the
  conversation on the current tag (the earliest entry in ROADMAP.md
  without a git tag), optionally updates GDD.md / ROADMAP.md, then
  generates the current tag's PLAN/STRUCTURE/SCENES/ASSETS at the project
  root. Explicit invocation only — use /gm-gdd.
disable-model-invocation: true
---

# GodotMaker GDD

$ARGUMENTS

You are running the design phase **for one tag at a time**. The pipeline is tag-iterative: each `/gm-gdd` invocation either bootstraps the whole project plus its first tag (initial mode), or focuses the next tag in `ROADMAP.md` (subsequent mode).

## Session Setup

**FIRST ACTION — before anything else:** Write `gdd` to `.godotmaker/current_role`.

## Resume Check

Read `.godotmaker/stage.jsonl` (treat as empty if missing) — each line is `{"role": X, "ts": Y}`.

- If `project.godot` does not exist → STOP. Tell user to run `/gm-scaffold` first.
- If the **last event** has `role == "gdd"` → STOP. Tell the user:
  > "GDD already completed for the current tag at {timestamp}. Recommended next: /gm-asset.
  > If you need to redo this step or have other plans, just tell me."
- Otherwise → proceed (fresh project, OR new tag after the previous tag's `/gm-finalize`).

## Mode Detection

Detect the mode by inspecting on-disk state — there is no flag:

- **Initial mode**: `ROADMAP.md` does NOT exist. (`GDD.md` may also be missing — if it is, this is a brand-new project.)
- **Subsequent mode**: `ROADMAP.md` EXISTS. Determine the **current tag** as follows:
  1. Read `ROADMAP.md`, list tag entries in declared order.
  2. Run `git tag --list 'v*'` (capture stdout).
  3. The current tag is the **earliest tag in ROADMAP that is not in `git tag --list`**.
  4. If every ROADMAP entry already has a git tag, STOP and inform the user the roadmap is exhausted — they must edit `ROADMAP.md` to add new entries before re-running `/gm-gdd`.

State the detected mode + (if subsequent) the current tag explicitly to the user as your first conversational message after Resume Check passes. They should never have to guess which tag they're working on.

## Hard Rules

1. **You CANNOT write game code (.gd/.tscn/.tres).** Code lives in workers in `/gm-build`.
2. **You CANNOT write to `assets/`.** Assets are produced in `/gm-asset`.
3. **Use AskUserQuestion for confirmation.** GDD must be explicitly confirmed by the user before generating ROADMAP / per-tag artifacts. ROADMAP must be explicitly confirmed before any artifact is written.
4. **MUST NOT skip the ROADMAP confirmation gate** — see Sub-stages below. Initial mode WITHOUT a confirmed ROADMAP cannot proceed to artifact generation; subsequent mode with a roadmap edit WITHOUT re-confirmation cannot proceed either.
5. **Subsequent mode does NOT append tag-N sections to STRUCTURE/SCENES/ASSETS.** It **overwrites** those root files with the current tag's scope. Prior tags' versions live in `docs/tags/<prev_tag>/`. The cross-tag accumulating files are only `GDD.md`, `ROADMAP.md`, and `MEMORY.md`.
6. **GDD design changes that contradict shipped tags MUST be reflected as PLAN refactor tasks.** When subsequent-mode interview reveals that a prior tag's behaviour now needs to change, the GDD update marks the old behaviour as `(superseded by ...)` rather than deleting it, AND the new PLAN.md gains an explicit refactor / removal task in the Main Build section.

## Sub-stages

### 1a — Interview & GDD update

Invoke the `game-planner` skill (`.claude/skills/game-planner/SKILL.md`).

- **Initial mode:** game-planner runs the full Socratic interview → produces fresh `GDD.md`.
- **Subsequent mode:** brief game-planner with:
  - Current tag id (e.g. `v0.2.0`)
  - The current ROADMAP.md entry for that tag (its bullet list)
  - The full existing `GDD.md` content
  - The previous tag's `docs/tags/<prev>/PLAN.md` Tag Mechanics list (so the conversation knows what already shipped)

  Game-planner asks the user: "We're about to plan {Tag}. ROADMAP currently says {bullets}. Do you want to keep that scope, adjust it, or change the underlying GDD design?" — and runs a focused interview. If the user changes design intent, game-planner updates `GDD.md` in place: new sections appended, replaced sections marked `(superseded by ...)`. Old GDD content is **never silently deleted**.

**Gate 1a:**
- [ ] `GDD.md` exists and (if subsequent mode) reflects the user's latest intent
- [ ] User has explicitly confirmed the GDD update via AskUserQuestion (or said "no changes needed")

### 1b — ROADMAP generation / adjustment

This sub-stage exists in BOTH modes but does different work.

**Initial mode:**
1. Read `GDD.md` (now confirmed).
2. Derive a tag list following the SemVer convention from `templates/ROADMAP.md`:
   - First tag is always `v0.1.0` and MUST deliver the playable closed loop (player can boot the game, exercise one core mechanic, reach one ending).
   - Subsequent tags add scope incrementally. Aim each tag at ~30 minutes of build wall-clock; MVP (v0.1.0) is allowed to exceed this because of setup overhead.
   - Tag count target: 3–8 tags total. More than 8 means each tag is too narrow to feel like progress; fewer than 3 means each tag is too broad to give early feedback.
3. Write a draft `ROADMAP.md` populated with this tag list.
4. **MANDATORY gate:** Use `AskUserQuestion` to ask the user:
   > "Here is the proposed roadmap. Is it OK to proceed with v0.1.0 as defined? You can also reorder, split, merge, or rewrite tags before we move on."
5. If user requests changes, edit `ROADMAP.md` accordingly and re-confirm. **Do NOT proceed to sub-stage 1c until the user explicitly confirms the ROADMAP.**

**Subsequent mode:**
1. Read existing `ROADMAP.md`.
2. If sub-stage 1a's interview revealed any roadmap-affecting decisions (user wants to reorder remaining tags, drop one, add one, or move scope around), edit `ROADMAP.md` accordingly. Tags that already have `git tag <tag>` are immutable — never modify their entries.
3. **If you modified ROADMAP.md in step 2:** use `AskUserQuestion` to re-confirm the updated roadmap before continuing. If you did not modify it, no extra confirmation needed.

**Gate 1b:**
- [ ] `ROADMAP.md` exists, with at least the v0.1.0 entry (initial) or the current tag's entry intact (subsequent)
- [ ] User has confirmed the roadmap (either fresh confirmation or "no changes" acknowledgement)
- [ ] Current tag id is established (initial: always `v0.1.0`; subsequent: per Mode Detection)

### 1c — Per-tag decomposition

After GDD + ROADMAP are confirmed, **delegate to the `decomposer` subagent**.

```
Agent({
  subagent_type: "decomposer",
  description: "Decompose current tag scope into PLAN/STRUCTURE/SCENES (and ASSETS rows for new assets this tag introduces)",
  model: "{decomposer_model from .godotmaker/config.yaml, default: sonnet}",
  prompt: "{brief below}"
})
```

Brief:

```
## Task: Decompose current tag into per-tag artifacts

### Mode
{initial | subsequent}

### Current Tag
{vX.Y.Z}

### Project Root
{absolute path to project root}

### GDD Path
{absolute path to GDD.md}

### Roadmap Path
{absolute path to ROADMAP.md}

### Templates Dir
{absolute path to .claude/templates/}

### Project.godot Path
{absolute path to project.godot}

### Manifest Path
{absolute path to assets/manifest.json — include only if file exists}

### Prior Tag Archives (subsequent mode only — empty list if no prior tags)
- v0.1.0: {absolute path to docs/tags/v0.1.0/}
- ...

### Inherited Mechanics (subsequent mode only)
{copy the union of Tag Mechanics from every prior tag's docs/tags/<prev>/PLAN.md;
each line must keep its `[<prev>-MN] description` format so decomposer can paste
them into the new PLAN.md's Inherited Mechanics section verbatim}

### Cross-Tag Refactor Hints (subsequent mode only — empty if none)
{any GDD changes confirmed in 1a that supersede prior-tag behaviour. For each:
- "<prior tag>'s <feature>" superseded by "<new design>"
- which files / systems likely need refactoring (best-effort guess; decomposer
  decides the exact PLAN tasks)}
```

The decomposer overwrites root `PLAN.md`, `STRUCTURE.md`, `SCENES.md` with the current tag's scope. For `ASSETS.md` it operates differently: in **initial mode** it writes the skeleton (Art Direction + empty tables); in **subsequent mode** it APPENDS new rows for assets this tag introduces (with `Tag = <current tag>`) and never modifies prior-tag rows. It does NOT touch `GDD.md`, `ROADMAP.md`, `MEMORY.md`, or any `docs/tags/` archive. It returns a short report; do NOT relay raw decomposer output to the user — run the gate first.

**Gate 1c:**
- [ ] `PLAN.md` exists with `**Tag:**` header matching the current tag, Tag Mechanics section populated, Inherited Mechanics section populated (or omitted entirely for v0.1.0), Task Status table with all `pending`
- [ ] `STRUCTURE.md` exists with `**Tag:**` header, scoped to this tag's additions / refactors
- [ ] `SCENES.md` exists with `**Tag:**` header, scoped to this tag
- [ ] `ASSETS.md` exists and any new rows are tagged correctly (per `templates/ASSETS.md` and `gm-asset/SKILL.md`)
- [ ] `TOC.md` updated (if decomposer touched it)

**Fallback when subagent doesn't finish.** If any gate item is unmet (whether the decomposer reported failure or just produced incomplete artifacts), do NOT respawn the subagent — instead, take over directly. Read whichever artifacts exist, identify the missing pieces, and write them using the same templates the decomposer would have used. The templates document their structure conventions.

**User-facing 1c summary (after gate + any fallback complete).** Build the announcement from the final on-disk state, not the raw decomposer report. Include: (a) decomposer's `Risk Tasks Identified` and `Key Architecture Decisions` (still useful as design rationale), (b) a fresh "files now on disk" line you observed yourself after fallback. If you took over for any file, say which ones — the user reads the actual files themselves.

**Cross-session backstop — what each hook actually does:**

- `stage_reminder.py` fires the moment you write `{"role": "gdd", ...}` to `.godotmaker/stage.jsonl`. It validates that the files declared in the `gdd` schema (`config/stage_schemas.json` → `gdd.files`) exist; if any are missing, it surfaces that to the lead before the gdd phase is considered done.
- `check_stage_prerequisites.py` fires when `/gm-build` (or `/gm-fixgap`) dispatches a worker — it re-validates the same schema. **It does NOT gate `/gm-asset`** (asset is not in `WORKER_DISPATCH_ROLES`); the asset phase relies on its own SKILL.md Resume Check instead.
- `check_completion.py` does NOT validate `gdd` at all — it only enforces worker-dispatch roles. Don't rely on it here.

So a partial 1c can still slip past `/gm-asset` if you skip the `stage_reminder` warning. The fallback above (lead takes over to fill missing files) is the primary safety net; the hooks are catch-up checks at later stages.

## Available Skills & Subagents

| Name | Type | Purpose |
|------|------|---------|
| game-planner | skill | Socratic interview → GDD generation/update (sub-stage 1a) |
| decomposer | subagent | Writes PLAN/STRUCTURE/SCENES/ASSETS for the current tag (sub-stage 1c) |
| godot-api | skill | Godot API reference (consumed by decomposer for project.godot edits) |

## When Done

After all three gates (1a, 1b, 1c) pass:

1. Append a line to `.godotmaker/stage.jsonl`: `{"role": "gdd", "ts": "<UTC ISO timestamp>", "tag": "<current tag>"}`. Read the existing file (treat as empty if missing), append the new event, and write the full file back.
2. Inform the user: `GDD complete for <Tag>. Recommended next: /gm-asset` (or skip straight to `/gm-build` if no new assets are needed for this tag — `/gm-asset` is manual and will simply STOP if there's nothing MISSING).
