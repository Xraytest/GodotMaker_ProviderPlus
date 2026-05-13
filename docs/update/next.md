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

- (WIP) Diagnostic log at `.godotmaker/log_agent_tool_debug.log` that records every phase of `log_agent_tool.py` so the next failure mode is localizable from artifacts.
- Each gm-* skill commits its stage outputs in When Done; new Stop hook `check_clean_workspace.py` reminds the agent once when the working tree is dirty at end of a skill.
- `tools/seal_tag.py` — three subcommands (`archive` / `reset` / `bundle`) replacing the per-call fs/git work in `/gm-finalize` Steps 4/5/7/8.
- `tools/run_verify.py` — wraps `/gm-verify`'s four mechanical checks (build / unit tests / lint / static check) into a single JSON-emitting command so the SKILL agent validates and reports instead of orchestrating four bash invocations.
- `hooks/log_compaction.py` — PreCompact hook that records `compaction` events to `metrics.jsonl` with `session_id`, `trigger` (manual/auto), and current pipeline role, so AAR analysis no longer has to scrape Claude Code's native session jsonl to know whether compaction fired.

## Changed

- Verifier and worker docs no longer prescribe authoring or running e2e — `/gm-evaluate` is the single source of truth for `e2e/`.

## Fixed

- (WIP) Rewire Agent prompt/output trace capture to `PreToolUse`/`PostToolUse` because the `SubagentStart` payload has no `prompt` field and silently wrote 0-byte traces.
- Drop the SubagentStop hook's e2e content requirement on worker reports, since `check_file_permissions` already forbids workers from writing `e2e/`.
- Move `project.godot.run/main_scene` retargeting from decomposer to `/gm-build`'s dispatching agent so headless runs between `/gm-gdd` and the entry-scene worker no longer flood logs with `Cannot open file`.
- Parallel workers under `isolation: "worktree"` are now actually isolated — briefs use cwd-relative paths, dispatching agent pre-commits, workers commit before reporting.
- fix the issue that `/gm-asset` exits early when every art row in `ASSETS.md` is `provided` but `references/scene_*.png` is still missing
- `godot-e2e` SKILL Critical Rules now flag `wait_process_frames` as a frame budget not wall-clock, and the Quick Start conftest reminds you to swap `/root/Main` for your project's entry-scene root
- `/gm-finalize` writes `final_report.json` and commits the tag archive before `git tag <Tag>`, so the tag points at a committed state including the final report (previously the tag landed on an uncommitted working tree).
- `/gm-finalize` partial-failure retries between Steps 4 and 8 now re-enter the skill instead of being misclassified as already-finalized.

## Removed
