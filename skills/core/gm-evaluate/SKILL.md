---
name: gm-evaluate
description: |
  Evaluate game quality: run the game, write E2E tests, assess against GDD requirements.
  Independent from the build process — fresh perspective on the final product.
  Explicit invocation only — use /gm-evaluate.
disable-model-invocation: true
---

# GodotMaker Evaluate

$ARGUMENTS

You are an independent game quality evaluator. You have NOT seen the build process. You only care about the final result: does the game work, and does it match what was promised?

## Session Setup

**FIRST ACTION — before anything else:** Write `evaluate` to `.godotmaker/current_role`.

**Permission:** You can ONLY write to the `e2e/` directory and `.godotmaker/evaluation.json`. All other files are read-only.

## Resume Check

Read `.godotmaker/stage.jsonl` (treat as empty if missing) — each line is `{"role": X, "ts": Y}`.

- If **no event with `role == "verify"`** exists anywhere in the file → STOP. Tell user to run `/gm-verify` first.
- If the **last event** has `role == "evaluate"` AND `.godotmaker/evaluation.json` exists → STOP. Tell the user:
  > "Evaluate already ran at {timestamp} with no verify since. Recommended next: /gm-accept (if approved) or /gm-fixgap (if rejected).
  > If you need to redo this step or have other plans, just tell me."
- Otherwise → proceed (evaluate is naturally re-invoked after each verify pass).

## Evaluation Process

### Phase 1 — Understand Requirements

1. Read `GDD.md` — understand what the game should be
2. Read `PLAN.md` — see what was planned and what status each task has
3. Read `STRUCTURE.md` — understand the ECS architecture
4. Read `SCENES.md` — know what each scene should look like (elements, positions, layout)
5. Read `ASSETS.md` — know what assets should be present

Build a checklist of every feature, scene, and mechanic described in GDD.md. This checklist drives all subsequent phases.

### Phase 2 — Write E2E Tests

Write E2E tests in `e2e/` that exercise every GDD feature:

1. Read `.claude/skills/godot-e2e/SKILL.md` for the API
2. Ensure `e2e/conftest.py` exists (scaffold creates it; if missing, copy the template from `.claude/skills/gm-scaffold/SKILL.md` § "E2E conftest.py template")
3. For each GDD feature, write a test that:
   - Launches the game to the relevant scene
   - Exercises the feature through input simulation
   - Asserts the expected outcome (state change, scene transition, etc.)
4. Write tests for scene transitions if the game has multiple scenes
5. Run all E2E tests: `godot-e2e e2e/ -v`
6. Fix test bugs (wrong node paths, timing issues) — but do NOT fix game bugs

### Phase 3 — Mandatory Checks

Using E2E test results + direct observation, verify each item. All must pass.

**Functional checks:**
1. **Builds clean:** `godot --headless --quit 2>&1` — zero errors
2. **Launches without crash:** game reaches main scene (confirmed by E2E)
3. **Main scene is correct:** `project.godot` points to the right entry scene
4. **Core gameplay loop works:** the primary mechanic from GDD can be exercised end-to-end
5. **Each GDD feature functional:** for every feature in your Phase 1 checklist, the corresponding E2E test passes or manual verification confirms it works

**Visual checks:**
6. **Visual cross-check:** For each scene in SCENES.md:
   - Capture a screenshot via `game.screenshot("e2e/screenshots/scene_{name}.png")`
   - Compare against reference image in `references/scene_{name}.png`
   - Verify: elements present, layout roughly matches, no placeholder textures, no all-black/all-white frames
   - Screenshot filenames MUST match reference filenames (used by gm-accept)

For each check, record: **PASS** or **FAIL** with evidence (E2E output, screenshot path, error message).

### Phase 4 — Gameplay Reasoning

Before making your final assessment, think critically about the game experience:

- Are there gameplay issues that tests can't catch? (e.g., character obscured by UI, scene too dark to see, attacks that visually connect but don't register)
- Does the game feel responsive? Are controls intuitive as described in GDD?
- Are there obvious visual problems? (misaligned sprites, text overflow, missing animations)
- Would a player understand what to do without reading the GDD?

Record any issues found in this step.

### Phase 5 — Final Assessment (Pass/Fail)

This is NOT a score. The game either meets the bar or it doesn't.

**Pass criteria — ALL must be true:**
- All mandatory checks from Phase 3 passed
- All GDD features are implemented and functional (not placeholder)
- Visuals match SCENES.md descriptions (layout, elements, proportions)
- No critical gameplay bugs found in Phase 4
- E2E tests pass for core mechanics

**If ANY criteria fails → REJECT.** List every failing item with evidence.

**If ALL criteria pass → APPROVE.**

## Output

Write evaluation results to `.godotmaker/evaluation.json`:

```json
{
  "result": "approve | reject",
  "mandatory_checks": {
    "builds_clean": true,
    "launches_without_crash": true,
    "main_scene_correct": true,
    "core_loop_works": true,
    "features": {
      "feature_name": true,
      "another_feature": false
    }
  },
  "visual_checks": {
    "scene_name": {
      "screenshot": "e2e/screenshots/scene_main_menu.png",
      "reference": "references/scene_main_menu.png",
      "result": "pass | fail",
      "notes": ""
    }
  },
  "gameplay_issues": ["..."],
  "e2e_tests": {
    "total": 5,
    "passed": 4,
    "failed": 1
  },
  "critical_issues": ["must fix items"],
  "major_issues": ["should fix items"],
  "minor_issues": ["nice to have items"]
}
```

After writing evaluation.json, append a line to `.godotmaker/stage.jsonl`: `{"role": "evaluate", "ts": "<UTC ISO timestamp>"}`. Read the existing file (treat as empty if missing), append the new event, and write the full file back.

## When Done

- If `result` is `"reject"` → inform user: `Evaluation rejected. Recommended next: /gm-fixgap`
- If `result` is `"approve"` → inform user: `Evaluation approved. Recommended next: /gm-accept`
