# Next Release

> **Contributors:** Every pull request MUST include an entry in this file describing the change.
> When a new version is released, this file will be archived as `vX.Y.Z.md` and a fresh copy will take its place.

## How to add an entry

Append your change under the appropriate category below. Use this format:

```
- Brief description of the change (#PR_NUMBER) — @author
```

If no category fits, add a new one following [Keep a Changelog](https://keepachangelog.com/) conventions.

---

## Added

## Changed

## Fixed

- **`stage.jsonl` event timestamps off the agent.** All ten `/gm-*` skills' "When Done" sections now invoke `tools/append_stage_event.py` (system clock + `O_APPEND`) instead of hand-writing the JSON. Fixes the fabricated and causally-violating timestamps observed in 2026-05-09 e2e fixgap / evaluate events.
- **Tag-pipeline migration backfills three schema gaps it originally shipped without.** `migrations/20260507120000_introduce_tag_based_pipeline.py` now adds the `Tag` column to `ASSETS.md`, a `MISSING` reference row per `## Scene:`, and a `## Tag Mechanics` section to `PLAN.md`. Targets that already applied this migration must drop the entry from `.godotmaker/applied_migrations.json` and re-publish to pick up the backfills.
- **PR template gates migration changes on a real publish-upgrade test.** Unit tests on synthetic projects had let the schema gaps above slip through; the new checklist forces a `tools/publish.py <target>` run on a pinned-old-version project before merge.

## Removed
