---
name: gm-finalize
description: |
  Seal the current tag: snapshot the per-tag working docs into
  docs/tags/<Tag>/, write a CHANGELOG entry, run `git tag`, and reset
  per-tag runtime state for the next /gm-gdd round. Does NOT package a
  release — that lives in a separate skill.
  Explicit invocation only — use /gm-finalize.
disable-model-invocation: true
---

# GodotMaker Finalize

$ARGUMENTS

You are sealing the **current tag** (vX.Y.Z) so the next `/gm-gdd` round can start cleanly. This is a per-tag operation, not a "the game is finished" operation. The user may continue to the next tag right after, or stop here — either way, this tag's deliverables are now archived and git-tagged.

## Session Setup

**FIRST ACTION — before anything else:** Write `finalize` to `.godotmaker/current_role`.

## Resume Check

Read `.godotmaker/stage.jsonl` (treat as empty if missing) — each line is `{"role": X, "ts": Y, ...}`.

- If `PLAN.md` does not exist or is missing the `**Tag:**` header → STOP. Tell the user the project is in a bad state; re-run `/gm-gdd` to regenerate the current tag's working docs.
- If **no event with `role == "accept"` and `decision == "accept"`** exists anywhere in the file → STOP. Tell user to run `/gm-accept` first.
  (Events with `decision == "fix"` or `decision == "done"` are trace records, not completions.)
- If `docs/tags/<Tag>/` already contains a full archive **and** `git tag <Tag>` already exists → STOP. Tell the user:
  > "Tag {Tag} already finalized. Run /gm-gdd to start the next tag, or stop here.
  > If you need to redo this step or have other plans, just tell me."
- Otherwise → proceed.

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

## Process

### 1. Read the current tag

Read `PLAN.md`, extract `**Tag:**` header value (e.g. `v0.2.0`). All later steps refer to this as `<Tag>`.

### 2. Quick Sanity Check

- `"<godot_path>" --headless --quit 2>&1` — builds clean
- `PLAN.md` — no `pending` or `in_progress` tasks; all `verified`
- `.godotmaker/evaluation.json` exists with `result: "approve"`

If any check fails, STOP and tell the user which one — finalize must not seal a broken tag.

### 3. Document Consistency Check (current tag scope)

For each per-tag document, verify it matches what was actually built **in this tag**. Do NOT update prior tags' archives.

- **GDD.md**: Cross-tag "north star". If the user changed design intent during this tag's gm-gdd round, GDD should already reflect it. Check that no claims about future tags have leaked in.
- **PLAN.md**: All tasks `verified`. Tag Mechanics + Inherited Mechanics sections present and complete.
- **STRUCTURE.md**: Components and Systems listed match what actually exists in code. Run a quick scan: list `extends Component` / `extends System` files and reconcile.
- **ASSETS.md**: Verify rows match `assets/` directory contents.
- **SCENES.md**: Scene descriptions match actual scenes added in this tag.
- **MEMORY.md**: Cross-tag accumulator. Append-only since the previous tag — don't rewrite history; if a previous discovery was later proven wrong, mark it `(superseded by …)` instead of deleting.

For any inconsistency: update the doc to match reality. Do NOT change code here — finalize is a paper-trail step.

### 4. Archive into `docs/tags/<Tag>/`

Create `docs/tags/<Tag>/` if it doesn't exist. Copy these files in (overwriting any earlier partial archive):

| Destination | Source |
|---|---|
| `docs/tags/<Tag>/GDD-snapshot.md` | `GDD.md` (full snapshot of north-star at this moment) |
| `docs/tags/<Tag>/PLAN.md` | `PLAN.md` |
| `docs/tags/<Tag>/STRUCTURE.md` | `STRUCTURE.md` |
| `docs/tags/<Tag>/SCENES.md` | `SCENES.md` |
| `docs/tags/<Tag>/MEMORY.md` | `MEMORY.md` (full cumulative state at this moment) |
| `docs/tags/<Tag>/evaluation-final.json` | `.godotmaker/evaluation.json` |

Do NOT archive `ASSETS.md`. Do NOT archive `.godotmaker/stage.jsonl`, `metrics.jsonl`, or `traces/` — those are runtime artifacts (metrics + traces accumulate cross-tag in `.godotmaker/`; stage gets reset in step 7).

### 5. Generate `docs/tags/<Tag>/CHANGELOG.md`

Write a per-tag changelog entry. Source material:

- ROADMAP.md entry for this `<Tag>` → headline + bullet features
- PLAN.md → Tag Mechanics list (mechanics that passed evaluation this round)
- PLAN.md task table → which subsystems / scenes / assets were added
- evaluation.json `minor_issues` → known limitations
- git log between previous tag and HEAD (if any prior tag exists) → file-level summary

Format:

```markdown
# Changelog — <Tag>

**Released:** <UTC ISO date>
**Theme:** <ROADMAP headline>

## Delivered mechanics

- [<Tag>-M1] <description>
- [<Tag>-M2] ...

## Added systems / scenes / assets

- <bulleted list pulled from PLAN.md>

## Refactored from prior tags (if any)

- <files / systems modified that belonged to a previous tag, with one-line reason>

## Known limitations

- <minor issues from evaluation.json that ship as-is>
```

### 6. Run `git tag <Tag>`

```bash
git tag <Tag>
```

If the tag already exists locally (e.g. retrying finalize after a partial failure), skip silently — the archive in step 4 is the ground truth, the tag just marks the commit. If git is unavailable in the project, log the gap and continue (the archive still seals the tag).

Do NOT push the tag. Pushing is a separate user decision.

### 7. Reset per-tag runtime state

Clear the working state so the next `/gm-gdd` starts on a clean slate:

- Truncate `.godotmaker/stage.jsonl` to empty
- Delete `.godotmaker/metrics_current.jsonl` (session-scoped; permanent log in `metrics.jsonl` stays)
- Leave alone: `.godotmaker/metrics.jsonl`, `.godotmaker/traces/`, `.godotmaker/config.yaml`, `.godotmaker/hooks/`, `.godotmaker/version`, `.godotmaker/evaluation.json` (will be overwritten by next gm-evaluate), `.godotmaker/current_role` (cleared in step 10 below — must stay set as `finalize` so steps 8/9's writes still match the finalize role's permission scope)

The root-level per-tag working docs (`PLAN.md`, `STRUCTURE.md`, `SCENES.md`) are **kept** at root. The next `/gm-gdd` subsequent-mode will overwrite them with the next tag's working set; until then they reflect what was just shipped.

### 8. Generate Final Report

Write `.godotmaker/final_report.json`:

```json
{
  "status": "tag_sealed",
  "tag": "<Tag>",
  "completed_at": "UTC timestamp",
  "archive_path": "docs/tags/<Tag>/",
  "git_tagged": true,
  "summary": {
    "tag_mechanics": ["<Tag>-M1", ...],
    "systems_added": [...],
    "components_added": [...],
    "test_count": {"unit": N, "e2e_tag": M, "e2e_regression": K}
  },
  "doc_updates": ["list of root docs updated in step 3"],
  "known_limitations": ["from MEMORY.md and evaluation minor_issues"]
}
```

`final_report.json` is **per-tag overwritten** — only the latest tag's report is kept at this path. Historical reports are recoverable from the `docs/tags/<Tag>/` archives via git history if needed.

This step MUST run before step 9: the `finalize` schema declares `final_report.json` as a required output, and `stage_reminder.py` validates declared files exist at the moment the stage event is appended. Writing the event first would be denied.

### 9. Append finalize event

From the project root run `python tools/append_stage_event.py finalize --tag=<Tag>` to append a `{"role": "finalize", "ts": "<server-generated UTC>", "tag": "<Tag>"}` line to `.godotmaker/stage.jsonl`. Do NOT hand-write the JSON or the timestamp — the helper exists so the timestamp comes from the system clock, not your own output.

> Note: this re-creates `stage.jsonl` after step 7 truncated it. The single finalize event is the only thing that lives in the new tag's stage.jsonl until /gm-gdd subsequent-mode adds its own event.

### 10. Clear current_role and inform user

Delete `.godotmaker/current_role` AFTER steps 8 and 9 have completed — those writes need the role lock in place so `check_file_permissions.py` keeps the finalize permission scope active for them.

Then print:

```
## Tag <Tag> Sealed

**{game_name}** — tag <Tag> archived and git-tagged.

- Archive: docs/tags/<Tag>/
- Git tag: <Tag> (local; not pushed)
- Tag mechanics delivered: {Tag Mechanics list}
- Doc updates this round: {list or "none needed"}
- Known limitations: {list or "none"}

Remaining tags in ROADMAP.md: {list of unshipped tags}

To start the next tag: /gm-gdd
To package this tag as a release: use the release skill (separate)
To stop here: just don't run anything else — the archive is permanent.
```

## What this skill explicitly does NOT do

- **No release packaging.** Building a distributable archive (zip / installer / web export) is the job of a separate release skill, invoked at the user's choice.
- **No `git push`.** The tag stays local until the user pushes it.
- **No code changes.** Finalize is paper-trail + archive only.
- **No cross-tag history rewrite.** Older tags' archives in `docs/tags/v0.X.Y/` are immutable from this skill's perspective.
