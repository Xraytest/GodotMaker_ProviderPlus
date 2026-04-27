# Frequently Asked Questions

---

## Getting started

### Do I need to know game development?

No. GodotMaker is designed for people who have a game idea but are not game developers. You describe what you want in plain English, confirm the design feels right when it's shown to you, and let the AI do the implementation. That said, you will need to read your `GDD.md` and say whether it captures what you meant — the AI writes it, but you approve it.

### Do I need a paid API key?

You need a Google API key (`GOOGLE_API_KEY`) for Gemini, which handles image generation and visual quality checking. This is required. Two optional keys add alternative providers: `XAI_API_KEY` for xAI Grok (cheaper image generation) and `TRIPO3D_API_KEY` for 3D model generation if you are making a 3D game.

Claude Code itself requires an Anthropic account with API access (or a Claude Pro / Team subscription with Claude Code enabled).

See the installation page for setup instructions.

### What Godot version do I need?

Godot 4.4 or later. GodotMaker does not support Godot 3.x or Godot 4.3 and below.

### How long does it take to make a game?

For a small game, expect roughly 30 minutes of your own time spread across several `/gm-*` commands — reading the GDD, confirming the design, checking the evaluation report, and accepting the result. The AI runtime (building, testing, generating art) runs in the background during each command and may take longer depending on your machine and network speed. More ambitious games scale with the number of tasks in your `PLAN.md`.

### Can I use C# instead of GDScript?

Yes. GodotMaker supports both GDScript and C#. ECS components and systems can be written in either language. Make sure you are using a .NET-enabled Godot build when working with C#.

---

## Pipeline behaviour

### What is a milestone?

A milestone is one complete pass through the pipeline: from `/gm-gdd` (write the design) through `/gm-finalize` (stamp it done). When you want to add a new feature or change direction, you start another milestone by running `/gm-gdd` again. `/gm-scaffold` runs only once per project and does not repeat between milestones.

### What if I want to stop halfway through?

You can stop at any point. The next time you open the project, the `session_start.py` hook reads `.godotmaker/stage.jsonl` to see where you left off, and the active role skill shows you a resume summary. Just run the same `/gm-*` command again to pick up where you stopped.

For a full walkthrough of recovery scenarios, see [Recovery & Resume](../04-troubleshooting/recovery-and-resume.md).

### Can I run two `/gm-*` commands at the same time?

No. Each `/gm-*` skill writes its name to `.godotmaker/current_role` when it starts, and hook scripts use that file to enforce write permissions. If a second command tried to start while one was already running, the file-permission hook would immediately start blocking unexpected writes. Run one command at a time and wait for it to complete.

### Why are some commands re-runnable and others are not?

`/gm-scaffold` is a once-per-project command — re-running it on an existing project would overwrite the project setup. `/gm-asset` is re-runnable within a milestone whenever new assets are needed. The roles from `/gm-build` onward follow the milestone cycle: they should run in order, and re-running one re-does that phase of the current milestone. `/gm-gdd` starts a new milestone cycle.

### What happens inside `/gm-build`?

`/gm-build` works through the task list in `PLAN.md` by dispatching a chain of sub-agents for each task: a **Worker** implements the code and tests, a **Verifier** builds the project headlessly and runs the tests, and a **Reviewer** checks for Godot-specific pitfalls. If the reviewer finds new issues they are added back to `PLAN.md` and picked up in the next batch. The `check_completion.py` hook refuses to let `/gm-build` end if any batch ran workers but skipped verifier or reviewer.

### Why does the AI need git worktrees?

When `/gm-build` runs multiple workers in parallel, each worker needs its own folder to write files into without conflicting with the others. Git worktrees let multiple working directories share the same repository history. This is also why `/gm-scaffold` creates an initial git commit — worktrees require at least one commit to exist.

---

## Quality and output

### Why doesn't my game look exactly like the GDD says?

AI code generation is not deterministic, and complex interactions between game systems can produce unexpected results. That is what `/gm-evaluate` and `/gm-fixgap` are for: the evaluator scores the running game against your GDD and produces a gap list, then fixgap dispatches workers to close each gap. Running this loop once is usually enough for a small game; larger games may benefit from a second pass.

### Can I edit the generated code by hand?

Yes, and your edits will be preserved. Be aware that if you run `/gm-build` again for a new milestone, it may add new tasks that touch the same files — so your edits could be extended or partially overwritten by new worker output. Keep your hand-edits focused and document them in `MEMORY.md` so the AI knows they were intentional.

### Where do I find screenshots and test results?

- Screenshots captured during evaluation: `e2e/screenshots/`
- Per-scene visual reference images: `e2e/screenshots/scene_<name>/`
- Evaluation scores and gap list: `.godotmaker/evaluation.json`
- Hook and pipeline metrics: `.godotmaker/metrics_current.jsonl`

### Why ECS instead of plain Godot scripts?

Plain Godot node scripts tend to mix data, logic, and scene structure in one file. As the game grows, these files get harder to change without breaking something. ECS separates concerns cleanly: data lives in components, logic lives in systems, and entities are just IDs that connect them. For AI-generated code this matters a lot — new behaviour is always a new component plus a new system, not an edit to an existing 1000-line script.

For a longer explanation, see [ECS in plain English](../02-concepts/ecs-in-plain-english.md).

### How do I know if the build succeeded?

After `/gm-verify` completes, the result is in `.godotmaker/verify_result.json`. Each worker's report also records whether its tests passed. If the Godot headless build fails or unit tests fail, the verifier sub-agent reports this and the issue is fed back to a worker for a fix.

---

## Cost and privacy

### Where does my game data go?

All game files live locally on your machine. AI calls go to whatever model provider Claude Code is configured for (typically Anthropic's API). Image generation calls go to Gemini (Google) or xAI depending on your configuration. No game content is stored on GodotMaker's servers because GodotMaker has no servers — it is a local framework.

### Is my game project mine?

Yes. GodotMaker only deploys files into your folder and then the AI fills them in. You own everything that gets generated. The GodotMaker framework source is available under its own license, but your game content and code are yours.

---

## Troubleshooting

### A hook keeps blocking me and I can't proceed.

Hooks have a built-in anti-deadloop limit. `check_completion.py` allows up to 5 consecutive blocks before force-allowing; `check_worker_report.py` allows up to 2 blocks per sub-agent. If you are hitting these limits repeatedly something in the pipeline has gone wrong — check the failing sub-agent's report for missing sections or malformed output.

For common hook errors and how to read them, see [Common problems](../04-troubleshooting/common-problems.md).

### I get "fatal: not a valid object name: HEAD" when a worker starts.

This means the project has no git commits yet. `/gm-scaffold` should have created one. Re-run `/gm-scaffold` or create an initial commit manually with `git commit --allow-empty -m "init"`.

### My evaluation score is low but the game seems fine to me.

The evaluator uses visual QA against per-scene reference images and the GDD description. If you skipped `/gm-asset`'s Step 3 (which generates `references/scene_*.png` files), the evaluator has no visual reference to compare against and will score conservatively. Run `/gm-asset` again to generate the missing references before re-evaluating.

### How do I roll back to a previous GodotMaker version?

Check out the older version tag in the GodotMaker repo, then re-publish with `--force`:

```bash
git checkout v0.1.0          # in the GodotMaker repo
python tools/publish.py --force /path/to/my-game
```

The `--force` flag skips the upgrade prompts and does a clean re-initialisation of the framework files in your project.

### The pipeline references "stages" but I only see `/gm-*` commands. What gives?

"Stage" was the original GodotMaker term for a pipeline step. The framework has been redesigned around 9 role-based commands with no central orchestrator. Some file names (like `stage.jsonl` and `stage_schemas.json`) still use the old word for continuity. Treat "stage" and "role" as synonyms when you see them in tool output or older docs. See also: *Stage vs Role* in the Glossary.
