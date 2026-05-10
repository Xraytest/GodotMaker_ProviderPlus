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

## Removed
