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
- `tools/publish.py` accepts `--agent claude-code|codex` and publishes the framework into the selected agent's project-local layout (`.claude/` or `.agents/`) instead of exporting both at once.
- Each gm-* skill commits its stage outputs in When Done; new Stop hook `check_clean_workspace.py` reminds the agent once when the working tree is dirty at end of a skill.
- `tools/seal_tag.py` — three subcommands (`archive` / `reset` / `bundle`) replacing the per-call fs/git work in `/gm-finalize` Steps 4/5/7/8.
- `tools/run_verify.py` — wraps `/gm-verify`'s four mechanical checks (build / unit tests / lint / static check) into a single JSON-emitting command so the SKILL agent validates and reports instead of orchestrating four bash invocations.
- `hooks/log_compaction.py` — PreCompact hook that records `compaction` events to `metrics.jsonl` with `session_id`, `trigger` (manual/auto), and current pipeline role, so AAR analysis no longer has to scrape Claude Code's native session jsonl to know whether compaction fired.

## Changed

- Asset generation now reads image provider and image/video model defaults from `.godotmaker/config.yaml`, with Gemini Nano Banana 2 as the shipped default.
- Verifier and worker docs no longer prescribe authoring or running e2e — `/gm-evaluate` is the single source of truth for `e2e/`.
- gecs gotcha G20: `@export var x: Node` fails on Component (extends Resource) — store Node refs as runtime `var` instead of `@export`.
- UI reviewer gotcha G11: Control under CanvasLayer needs explicit `layout_mode = 1` — anchor presets are silently ignored when `layout_mode` defaults to 0.
- `visual-qa` SKILL now lists each mode's exact argv shape in a decision table and rejects ambiguous shapes (e.g. `--screenshot ... --requirements ...`) instead of degrading to Question mode.
- `/gm-evaluate` Phase 4 must populate `phase4_review` with at least one `{category, verdict}` entry (categories picked per game) so the gameplay-reasoning step can no longer be silently skipped; `gameplay_issues` remains as a flat mirror for `/gm-fixgap`.
- `SCENES.md` template carries a per-scene `Acceptance criteria` block; the decomposer populates it from PLAN tag mechanics and `/gm-evaluate` pastes it verbatim into the visual-qa `Verify:` field.
- `/gm-evaluate` and `visual-qa` now tell VQA to avoid prior-history inference for deterministic setup screenshots.
- gecs `patterns.md` documents the pure-static helper convention (`*_math.gd` / `*_logic.gd` next to a System) and the `simulate_*` static seam on Systems — both used as the shared entry point for unit tests and e2e drivers.
- `worker-dispatch.md` "When to parallelize" now includes a batch design rule: inspect every pending task's Affected files and group disjoint sets up to 3-wide, rather than dispatching task-by-task.
- `gdunit-driver` SKILL adds a "Stub design" rule: a unit-test stub class must expose every property and method the system-under-test reads or calls on it, with a NodeRef-style WRONG/RIGHT example and a grep-before-submit check.
- `decomposer` Step 5 patches `project.godot` for pixel-art games (detected from GDD §4): 480×270 viewport, 1920×1080 window override, integer stretch, Nearest filter, snap-to-pixel.
- `/gm-gdd` initial mode now starts with a freeform user concept intake before structured GDD confirmation, so the interview can skip already-answered questions.
- `/gm-gdd` now decomposes in two phases so PLAN is finalized before architecture and scene/asset packages read its task and mechanic mappings.
- `check_project.py --build` now fails when `godot_path` is missing because headless parse is part of the scaffold build gate.
- Godot verification tools now prefer Godot's Windows console sibling for headless runs.
- GdUnit verification commands now use the official `res://addons/gdUnit4/bin/GdUnitCmdTool.gd --add res://test/` form and ignore generated `reports/`.
- Generated projects now include `.gitattributes` rules that normalize text line endings and keep Windows scripts on CRLF.
- Generated projects now register the `godot-e2e` `AutomationServer` autoload, and `check_project.py --build` verifies it.
- Codex runtime mapping now explicitly maps shared `.claude/godotmaker.yaml` config reads to `.agents/godotmaker.yaml`.
- Verifier dispatch now passes the configured Godot executable path into Godot commands.

## Fixed

- (WIP) Rewire Agent prompt/output trace capture to `PreToolUse`/`PostToolUse` because the `SubagentStart` payload has no `prompt` field and silently wrote 0-byte traces.
- Drop the SubagentStop hook's e2e content requirement on worker reports, since `check_file_permissions` already forbids workers from writing `e2e/`.
- Move `project.godot.run/main_scene` retargeting from decomposer to `/gm-build`'s dispatching agent so headless runs between `/gm-gdd` and the entry-scene worker no longer flood logs with `Cannot open file`.
- Parallel workers under `isolation: "worktree"` are now actually isolated — briefs use cwd-relative paths, dispatching agent pre-commits, workers commit before reporting.
- fix the issue that `/gm-asset` exits early when every art row in `ASSETS.md` is `provided` but `references/scene_*.png` is still missing
- `godot-e2e` SKILL Critical Rules now flag `wait_process_frames` as a frame budget not wall-clock, and the Quick Start conftest reminds you to swap `/root/Main` for your project's entry-scene root
- Scaffold and godot-e2e conftest templates now pass configured `godot_path` into `GodotE2E.launch`.
- Generated project `.gitignore` files now ignore Python bytecode so running `tools/*.py` does not stage `tools/__pycache__/*.pyc`.
- `/gm-finalize` writes `final_report.json` and commits the tag archive before `git tag <Tag>`, so the tag points at a committed state including the final report (previously the tag landed on an uncommitted working tree).
- `/gm-finalize` partial-failure retries between Steps 4 and 8 now re-enter the skill instead of being misclassified as already-finalized.
- `tools/publish.py` registers `Bash(<godot_path>:*)` in `.claude/settings.json` so headless godot invocations no longer prompt for permission, including in sub-agent worktrees (the user-level `settings.local.json` is gitignored and doesn't propagate).
- worker.md and the parallel merge procedure run `godot --headless --import` (not `--quit`) after new `class_name` declarations so the class cache stays consistent across worker worktrees and main.
- `/gm-evaluate` halts with a `critical_issue` instead of degrading to Question mode when `references/scene_*.png` is missing.
- `/gm-evaluate` records every visual-qa call in `visual_checks.<scene>.vqa_calls[]`; any agent-side override of the recorded verdict lands in `.notes` so the chain from initial call to final `result` stays auditable.
- `visual-qa`, `/gm-evaluate`, and `/gm-fixgap` no longer turn style-only reference mismatches into blocking visual tasks when the acceptance criteria already pass.
- `visual_qa.py` now reads prompt templates as UTF-8 on Windows.
- `/gm-evaluate` now writes VQA debug logs under `e2e/screenshots/` while `visual-qa` keeps its standalone default log path.

## Removed
