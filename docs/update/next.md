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

- New `gdd-auditor` subagent — independent reviewer that audits the draft GDD against a 9-category checklist (state/lifecycle, failure recovery, win/loss specifics, onboarding, balance numbers, feedback gaps, mechanic interactions, asset scope, skipped sections) and returns 5-8 follow-up questions per round.

## Changed

- `game-planner` skill now runs **two fixed audit rounds** after synthesizing the GDD draft (Rounds 6-7) before showing it to the user. Each audit batch-asks 5-8 questions to fill blind spots that single-pass interviews leak. Pattern follows GSD's Generator-Verifier loop with fresh-context audit rather than self-critique.

## Fixed

## Removed
