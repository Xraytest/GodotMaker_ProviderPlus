---
name: gm-evaluate
description: |
  Evaluate the current tag's quality: enforce the playable-closed-loop
  gate, maintain a single cross-tag e2e/ suite that always reflects the
  current game (add tests for new mechanics, prune tests for mechanics
  this tag deliberately removed), and reason about gameplay quality.
  Independent from the build process — fresh perspective on the final
  product. Explicit invocation only — use /gm-evaluate.
disable-model-invocation: true
---

# GodotMaker Evaluate

$ARGUMENTS

You are an independent game quality evaluator. You have NOT seen the build process. You only care about the final result for the **current tag**: does the game (as it stands at this tag) deliver every mechanic the project has shipped so far — including the ones this tag adds, and the inherited ones from previous tags that should still work?

E2E tests live in **a single `e2e/` directory** that always reflects the current state of the game. There is no per-tag e2e partitioning: when a tag adds a mechanic you add a test; when a tag deliberately removes a mechanic the corresponding refactor task in PLAN's Main Build prunes the test in the same change. You maintain `e2e/` so it matches the union of every still-supported mechanic listed across the current PLAN's Tag Mechanics + Inherited Mechanics.

## Session Setup

**FIRST ACTION — before anything else:** Write `evaluate` to `.godotmaker/current_role`.

**Permission:** You can write to `e2e/`, `.godotmaker/evaluation.json`, and append to `.godotmaker/stage.jsonl` (plus `.godotmaker/current_role` set during Session Setup). All other files are read-only.

## Resume Check

Read `.godotmaker/stage.jsonl` (treat as empty if missing) — each line is `{"role": X, "ts": Y}`.

- If **no event with `role == "verify"`** exists anywhere in the file → STOP. Tell user to run `/gm-verify` first.
- If `PLAN.md` is missing the `**Tag:**` header → STOP. Tell user the file is stale and to re-run `/gm-gdd` to regenerate it for the current tag.
- If the **last event** has `role == "evaluate"` AND `.godotmaker/evaluation.json` exists → STOP. Tell the user:
  > "Evaluate already ran at {timestamp} with no verify since. Recommended next: /gm-accept (if approved) or /gm-fixgap (if rejected).
  > If you need to redo this step or have other plans, just tell me."
- Otherwise → proceed (evaluate is naturally re-invoked after each verify pass).

## Evaluation Process

### Phase 1 — Understand Requirements

Read in order:

1. `PLAN.md` — extract **Tag:** header (call it `<Tag>`), Tag Mechanics list, Inherited Mechanics list, Main Build refactor tasks (the latter tells you which prior-tag mechanics this tag intentionally removes)
2. `GDD.md` — design intent (north star); cross-reference Tag Mechanics against the relevant GDD sections
3. `STRUCTURE.md` — current tag's ECS architecture
4. `SCENES.md` — current tag's scenes
5. `ASSETS.md` — cross-tag asset manifest
6. `ROADMAP.md` — confirm `<Tag>` is the entry being worked on (it should be the earliest entry without a `git tag`)

Build a single **expected-mechanics checklist** = (every `[<Tag>-MN]` from Tag Mechanics) ∪ (every `[<prev>-MN]` from Inherited Mechanics). This is the union of mechanics the game must currently support. The corresponding test files in `e2e/` must cover this checklist exactly — no more, no less.

### Phase 2 — Maintain the e2e/ suite

E2E tests live in a flat `e2e/` directory (no per-tag subdirectories). Each test file is named after the mechanic id it covers, e.g. `e2e/test_v0.1.0_M1_wasd_movement.gd` — the mechanic id in the filename keeps the test→ID mapping mechanical and stable as later tags inherit it.

1. Read `.claude/skills/godot-e2e/SKILL.md` for the API.
2. Confirm `e2e/conftest.py` exists at the e2e root (created by gm-scaffold).
3. **Add tests for new Tag Mechanics:** for each `[<Tag>-MN]` in PLAN.md that does not yet have a test file in `e2e/`, write `e2e/test_<tag_slug>_M<N>_<mechanic_slug>.gd` (or `.py`). The test must assert the **observable behaviour** named in the mechanic line, not internal state.
4. **Verify Inherited Mechanic tests still exist:** for each `[<prev>-MN]` in PLAN.md's Inherited Mechanics, the corresponding test file from when that prior tag shipped must still be in `e2e/`. If a file is missing (e.g. accidentally deleted), restore it by reading `docs/tags/<prev>/PLAN.md` and re-implementing the test.
5. **Prune tests for removed mechanics:** if PLAN's Main Build has a refactor task that removes a prior-tag mechanic (and that mechanic id therefore does NOT appear in this tag's Inherited Mechanics list), delete the corresponding `e2e/test_*.gd` file. Removal is intentional, refactor task is the audit trail.
6. **Add scene-transition tests** for new scenes added in this tag.
7. Run the full suite: `godot-e2e e2e/ -v`
8. Fix test bugs (wrong node paths, timing issues) — but do NOT fix game bugs; those are Phase 3+ findings.

After this phase the `e2e/` directory must contain exactly one test file per mechanic id in the expected-mechanics checklist (Phase 1), plus scene-transition tests. Stale files for mechanics that no longer appear anywhere are a Phase 3 critical_issue.

### Phase 3 — Mandatory Checks

All of these must pass for `result == "approve"`. Failure of any is a `critical_issue`.

**Playable closed loop (composite hard gate):**
1. **Builds clean:** `godot --headless --quit 2>&1` — zero ERROR lines.
2. **Boots into main scene:** `project.godot` points to the right entry scene; the entry scene loads without crash (confirm via E2E).
3. **At least one core mechanic runs end-to-end:** at least one mechanic in the expected-mechanics checklist has a passing E2E test in `e2e/`.
4. **At least one of {death, win, exit} ending exists and is reachable:** confirmed by either an E2E test that triggers it, or by static evidence (a scene transition / `quit()` call wired to a UI element).

**Mechanics gate (covers both new and inherited):**
5. Every entry in the expected-mechanics checklist has a corresponding test in `e2e/` AND that test passes. Each PASS/FAIL recorded against the mechanic id. A failing inherited test is just as critical as a failing tag test — both block approval.
6. The `e2e/` directory must NOT contain test files for mechanic ids absent from the checklist (orphan tests). Fix by either re-adding the missing mechanic to PLAN's Inherited Mechanics, or pruning the orphan test (whichever matches actual game state).

**Visual cross-check (per scene listed in SCENES.md):**
7. Capture a screenshot via `game.screenshot("e2e/screenshots/scene_{name}.png")`. For scenes with motion/animation, capture a frame sequence per `.claude/skills/screenshot/SKILL.md` § "Frame Sequence for VQA Dynamic Mode". Screenshots overwrite per run (they're verification artifacts, not history; `e2e/screenshots/` is gitignored or sparingly committed at the user's choice).
8. Compare against the reference image in `references/scene_{name}.png` by invoking the `visual-qa` skill — do not eyeball it yourself:
   ```
   # Static scene
   Skill(skill="visual-qa") "Check references/scene_{name}.png against e2e/screenshots/scene_{name}.png — Goal: {scene goal from SCENES.md}, Requirements: {key elements + layout}, Verify: no placeholder textures, no all-black/all-white frames, layout matches reference."

   # Dynamic scene (frame sequence in per-scene subdir)
   Skill(skill="visual-qa") "Check references/scene_{name}.png against e2e/screenshots/scene_{name}/frame_*.png — Goal: ..., Requirements: ..., Verify: motion is fluid, no stuck entities, animation matches movement."
   ```
   - Verdict mapping: `fail` → critical_issue; `warning` → major_issue; `pass` → recorded under `visual_checks`.
   - Backend defaults to Gemini Flash; pass `--native` for Claude vision or `--both` for aggregated verdict if a check is ambiguous.

For each check, record: **PASS** or **FAIL** with evidence (E2E output, screenshot path, error message).

### Phase 4 — Gameplay Reasoning

Before final assessment, think critically about the game experience. Tests can't catch:

- Character obscured by UI / camera framing wrong
- Scene too dark to see
- Attacks that visually connect but don't register
- Controls that are technically responsive but feel sluggish
- Player has no idea what to do without the GDD in front of them

Record any such issues. These become `gameplay_issues` in the output.

### Phase 5 — Final Assessment (Pass/Fail)

This is NOT a score. The tag either ships or it doesn't.

**Pass criteria — ALL must be true:**
- All Phase 3 mandatory checks pass (playable closed loop + mechanics gate + visual checks)
- No critical_issues unaddressed
- Every mechanic in the expected-mechanics checklist has a passing test in `e2e/`
- No orphan test files in `e2e/` (every test maps to a mechanic still in PLAN)

**If ANY criteria fails → REJECT.** List every failing item with evidence; the gm-fixgap loop will pick them up.

**If ALL criteria pass → APPROVE.**

## Output

Write evaluation results to `.godotmaker/evaluation.json`:

```json
{
  "tag": "<Tag>",
  "result": "approve | reject",
  "playable_closed_loop": {
    "builds_clean": true,
    "boots_main_scene": true,
    "at_least_one_mechanic_e2e": true,
    "at_least_one_ending_reachable": true
  },
  "tag_mechanics": {
    "<Tag>-M1": "pass",
    "<Tag>-M2": "fail"
  },
  "inherited_mechanics": {
    "v0.1.0-M1": "pass",
    "v0.1.0-M2": "pass"
  },
  "visual_checks": {
    "<scene_name>": {
      "screenshot": "e2e/screenshots/scene_<name>.png",
      "reference": "references/scene_<name>.png",
      "result": "pass | fail | warning",
      "notes": ""
    }
  },
  "e2e_tests": {"total": 0, "passed": 0, "failed": 0},
  "orphan_tests": [],
  "gameplay_issues": ["..."],
  "critical_issues": ["must fix items"],
  "major_issues": ["should fix items"],
  "minor_issues": ["nice to have items"]
}
```

After writing evaluation.json, append a line to `.godotmaker/stage.jsonl`: `{"role": "evaluate", "ts": "<UTC ISO timestamp>", "tag": "<Tag>"}`. Read the existing file (treat as empty if missing), append the new event, and write the full file back.

## When Done

- If `result` is `"reject"` → inform user: `Evaluation rejected for <Tag>. Recommended next: /gm-fixgap`
- If `result` is `"approve"` → inform user: `Evaluation approved for <Tag>. Recommended next: /gm-accept`
