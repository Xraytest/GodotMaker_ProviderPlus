# Common Problems

Quick reference: symptom, cause, fix. If your problem involves a crashed or interrupted session, see [Recovery and Resume](recovery-and-resume.md) instead.

---

## Setup problems

### `GOOGLE_API_KEY not set`

**Symptom** (from `check_env.py`):

```
[FAIL] GOOGLE_API_KEY not set (required for image gen + VQA). Get one: https://aistudio.google.com/apikey
```

**Cause:** The environment variable is missing from your shell session. GodotMaker needs it to generate art and run visual quality checks.

**Fix:** Get a key at https://aistudio.google.com/apikey, then set it in your terminal before launching Claude Code:

```bash
# macOS / Linux
export GOOGLE_API_KEY=your-key-here

# Windows (PowerShell)
$env:GOOGLE_API_KEY = "your-key-here"
```

To make it permanent, add the export line to your shell profile (`~/.bashrc`, `~/.zshrc`, or Windows System Environment Variables).

---

### Godot not found or wrong version

**Symptom:**

```
[WARN] Godot not found on PATH. Provide the full path when running publish,
       or add it to PATH.
```

or:

```
[FAIL] Godot 4.3.x too old (>= 4.4 required)
```

**Cause:** Godot 4.4 or later is not installed, or its folder is not on your system PATH.

**Fix:**

1. Download Godot 4.4+ from https://godotengine.org/download
2. Either add its folder to PATH, or open `.claude/godotmaker.yaml` in your game project and set the `godot_path` key to the full path of the Godot executable.

Verify with:

```bash
python tools/check_env.py
```

---

### Claude Code not found

**Symptom:**

```
[FAIL] Claude Code not found. Install: npm install -g @anthropic-ai/claude-code
```

**Cause:** The `claude` command is not on PATH. Claude Code is installed as a Node.js package.

**Fix:**

```bash
npm install -g @anthropic-ai/claude-code
claude --version   # should print a version number
```

If `npm` itself is missing, install Node.js 18+ from https://nodejs.org first.

---

### Workers fail to commit — Git identity not set

**Symptom:** A worker sub-agent errors out with a message like `Author identity unknown` or `git commit` refuses to run.

**Cause:** Git requires `user.name` and `user.email` to create commits. Worker sub-agents commit code on your behalf.

**Fix:**

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

Confirm with `python tools/check_env.py` — both should show `[PASS]`.

---

## Pipeline gate problems

These messages appear when you try to run a `/gm-*` command out of order. Each role checks that the previous required role finished before it starts.

---

### "Role 'gdd' has not completed yet — run /gm-gdd first"

**Symptom:** You ran `/gm-build` and got a hook block saying the `gdd` role is missing.

**Cause:** `/gm-build` needs a complete Game Design Document to know what to build. It checks `.godotmaker/stage.jsonl` for a `gdd` completion event, and/or checks that the GDD output files (`GDD.md`, `PLAN.md`, etc.) exist.

**Fix:** Run `/gm-gdd` and let it finish before running `/gm-build`.

---

### "Role 'evaluate' has not completed yet — run /gm-evaluate first"

**Symptom:** You ran `/gm-fixgap` and got a hook block.

**Cause:** `/gm-fixgap` needs an evaluation result to know what to fix. It checks for the `evaluate` completion event and for `.godotmaker/evaluation.json`.

**Fix:** Run `/gm-evaluate` and let it finish, then run `/gm-fixgap`.

---

### "Build already completed for this milestone..."

**Symptom:**

```
Build already completed for this milestone at <timestamp>. Recommended next: /gm-verify.
If you need to redo this step or have other plans, just tell me.
```

**Cause:** All tasks in `PLAN.md` are already in `verified` state. The skill detected no remaining work.

**Fix:** If you genuinely want to proceed, tell Claude Code "continue to /gm-verify" or run `/gm-verify`. If you think there is more to build, open `PLAN.md` and check whether tasks that should be `pending` are already marked `verified` — something may have been marked done prematurely.

---

### "Evaluate already ran... Recommended next: /gm-accept or /gm-fixgap"

**Cause:** `.godotmaker/evaluation.json` already exists and no new `/gm-verify` has run since. The evaluator won't re-run if the game hasn't changed.

**Fix:** Decide which direction to go: run `/gm-accept` to review results and approve, or `/gm-fixgap` if you want to fix issues. If you genuinely need to re-evaluate (e.g., you hand-edited code), tell Claude Code "redo the evaluation" and it will proceed.

---

### "Cannot finish 'build' role — diligence issues: Dispatched N workers but 0 verifiers"

**Symptom:** The session is blocked from ending, with a message about missing verifiers or reviewers.

**Cause:** `/gm-build` dispatched worker sub-agents but the session tried to end before running a verifier and reviewer round. The `check_completion.py` hook enforces this — workers alone don't count as done.

**Fix:** Tell Claude Code to continue: "run the verifier and reviewer now." The skill will dispatch them and the block will clear once they complete. Do not close the session manually — let the verification round finish.

---

## Build problems

### Headless build fails with class_name conflicts

**Symptom:** The Godot headless build step exits with an error like `Duplicate class name` or `Class name already exists`.

**Cause:** Two `.gd` files declared the same `class_name`. Godot treats class names as globally unique.

**Fix:**

```bash
python tools/check_classname.py <path-to-game>
```

This lists every `class_name` in the project and flags duplicates. Rename one of the conflicting classes (in the `.gd` file and any files that reference it).

---

### Workers seem to succeed but tests never run

**Symptom:** Build finishes, but you notice no test results were reported — or the hook flagged a worker report as "content-light."

**Cause:** `check_worker_report.py` validates that worker and verifier reports include real test output, not placeholder text. A report that says "tests passed" without evidence is blocked.

**Fix:** This usually self-corrects — the hook forces a retry. If it loops, tell Claude Code "the worker report is incomplete; retry the verifier." You can also inspect recent metrics:

```bash
cat .godotmaker/metrics_*.jsonl | grep HOOK_BLOCK
```

---

### Reviewer was skipped because the session ended

**Symptom:** `check_completion.py` blocks the next session start, or you notice from the metrics that a reviewer was never dispatched.

**Cause:** The session closed before the reviewer round ran. The hook will remind the skill when the session resumes.

**Fix:** Start a new Claude Code session and run `/gm-build` again. The Resume Check will see that tasks are in `completed` (not `verified`) state and will dispatch the reviewer round to finish.

---

### Worker died mid-task

**Symptom:** A worker sub-agent timed out or errored. Its task is stuck in `in_progress` in `PLAN.md`.

**Cause:** Sub-agents can fail due to long-running code generation, network issues, or context limits.

**Fix:** Open `PLAN.md` and manually change the stalled task's status from `in_progress` back to `pending`. Then run `/gm-build` again — the skill will pick up pending tasks and redispatch.

---

## Asset problems

### Image generation fails

**Symptom:** `/gm-asset` reports an error like `API quota exceeded`, `invalid API key`, or a network timeout during image generation.

**Causes and fixes:**

| Symptom | Cause | Fix |
|---------|-------|-----|
| `invalid API key` | `GOOGLE_API_KEY` is wrong or expired | Get a new key at https://aistudio.google.com/apikey |
| `quota exceeded` | Rate limit hit | Wait a few minutes, then re-run `/gm-asset` |
| Network timeout | Connectivity issue | Check your internet connection; re-run `/gm-asset` |

You can also run the generator directly to test it in isolation:

```bash
python tools/asset_gen.py
```

---

### Generated art doesn't look right

**Cause:** AI image generation is probabilistic — results vary run to run.

**Fix:** Re-run `/gm-asset`. Each run regenerates only assets that are missing or that you explicitly flag for regeneration. Alternatively, drop your own image files into `assets/` (matching the names listed in `ASSETS.md`) and run `/gm-asset` again — the analyst sub-agent will detect your files and skip generation for those entries.

---

### User wants to use their own art

**Fix:** Place your image files in `assets/` using the filenames listed in `ASSETS.md`. Then run `/gm-asset` — an analyst sub-agent will inspect each file, verify dimensions and format, and update `ASSETS.md` to mark those entries as provided. You do not need to delete any files; already-present assets are never overwritten.

---

## Evaluator problems

### Game crashes during evaluation

**Cause:** A code bug causes Godot to crash. `/gm-evaluate` records what it observed before the crash in `.godotmaker/evaluation.json`, including screenshots and partial test results.

**Fix:** The evaluator will automatically assign a low score and write a failure reason. Run `/gm-fixgap` — it reads `evaluation.json` and dispatches workers to address the crash. If the crash repeats across multiple fix iterations, open `evaluation.json` and look at the `issues` array for the specific error message to diagnose manually.

---

### Evaluation score too low to accept

**Symptom:** `/gm-evaluate` finishes, but the score is below the acceptance threshold. `/gm-accept` shows a "reject" recommendation.

**Fix:** Run `/gm-fixgap` to address the issues listed in the evaluation. After fixgap completes, run `/gm-verify` then `/gm-evaluate` again. You can repeat this loop as many times as needed. When the score is acceptable, run `/gm-accept` and confirm.

---

## Publish and version problems

### "MAJOR upgrade requires --force"

**Symptom:** Running `python tools/publish.py <target>` stops with a message about a MAJOR version bump.

**Cause:** The GodotMaker repo version and the version installed in your game project differ by a major version number. Major bumps may include breaking changes.

**Fix:** Read `CHANGELOG.md` to understand what changed, then run with the force flag if you want to proceed:

```bash
python tools/publish.py --force <target>
```

Note that `--force` overwrites `.claude/settings.json` in your game project. Back it up if you have customized it.

---

### Downgrade blocked

**Symptom:** `publish.py` refuses to install an older version of GodotMaker over a newer one.

**Cause:** Installing an older version over a newer one would downgrade the hook scripts and skills, which can break assumptions already baked into the project's `.godotmaker/stage.jsonl` timeline.

**Fix:** This is intentional. If you need to revert, restore from a git snapshot of your game project. Downgrades are not supported via `publish.py`.

---

### Migration script failed mid-chain

**Symptom:** A migration script printed an error and stopped partway through any non-MAJOR publish that runs pending migrations (PATCH, MINOR, or SAME-version republish).

**Fix:** Check the error message, fix the underlying issue (usually a missing file or wrong path), then re-run:

```bash
python tools/migrate.py <target>
```

Migration scripts are designed to be re-run safely — already-completed steps are recorded in `.godotmaker/applied_migrations.json` and skipped on the next run. If you are unsure which step failed, run `python tools/check_project.py <target>` to see the current state of required files.

---

### `applied_migrations.json` is corrupt

**Symptom:** Publish or `migrate.py` aborts with `TrackerCorruptionError: ... cannot parse JSON` or `... missing required field` or `... source must be one of ...`.

**Fix:** The applied-tracker file (`<target>/.godotmaker/applied_migrations.json`) is unreadable or its schema is wrong. Three recovery options:

1. **Restore from VCS** if the user committed it: `git checkout <target>/.godotmaker/applied_migrations.json`. (Note: GodotMaker's default `.gitignore` excludes this file, so VCS will only have it if you opted to track it explicitly.)
2. **Restart tracking from current state**: `python tools/migrate.py <target> --baseline`. Marks every current `migrations/<YYYYMMDDhhmmss>_<slug>.py` as applied without executing them — appropriate when the actual project state matches the latest format.
3. **Delete the file**: `rm <target>/.godotmaker/applied_migrations.json`. Treats the project as a legacy target on the next publish — see the `LegacyTargetWithMigrationsError` entry below for what happens then.

The system raises an explicit error here (instead of silently treating the tracker as empty) because a silent fallback would re-run every historical migration on the next publish — potentially corrupting state.

---

### `LegacyTargetWithMigrationsError`

**Symptom:** Publish or `migrate.py` aborts with `LegacyTargetWithMigrationsError: ... has .godotmaker/version ... but no applied_migrations.json, AND there are N migration script(s) on disk.` (Exit code 3 from `publish.py`.)

**Why it happens:** Your target was published by a pre-tracking GodotMaker version (so it has `.godotmaker/version` but no `applied_migrations.json`), and the GodotMaker version you're upgrading to ships migration scripts. We can't safely guess whether those scripts were already reflected in the target's old state or still need to run — silently picking either answer risks corrupting your project (auto-skipping required cleanup, or re-running migrations that have already been applied).

**Fix:** Pick the recovery option that matches your project's reality:

1. **Project is on the latest format already** (e.g., you've been keeping it manually in sync, or this is a freshly cloned repo): `python tools/migrate.py <target> --baseline`. Marks every current migration as applied without executing them, then re-run publish.
2. **Project genuinely pre-dates these migrations and you want them to actually run**: create an empty tracker manually so publish treats this as a normal "fresh tracker" upgrade. Use the cross-platform Python form below — `echo '{"applied": []}' > file` works on bash but on **Windows PowerShell 5.1** it writes UTF-16 LE with BOM, which the next publish will reject as `TrackerCorruptionError`.
   ```bash
   python -c "open(r'<target>/.godotmaker/applied_migrations.json', 'w', encoding='utf-8').write('{\"applied\": []}')"
   ```
   Then re-run publish — the migrations will go through the normal pending-application path.

> Why no `--force` recovery? `publish.py --force` only triggers the full cleanup loop on MAJOR upgrades. For PATCH/MINOR/SAME the `--force` path still calls `run_migrations()` and will hit the same `LegacyTargetWithMigrationsError` again. Use options 1 or 2 above.

This error is by design, not a bug — the previous behaviour silently auto-baselined legacy + migrations, which could skip required cleanup work without any signal.
