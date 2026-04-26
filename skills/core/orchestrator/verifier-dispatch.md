# Verifier Dispatch Protocol

When dispatching a verifier, fill in this EXACT template.

**Agent definition:** `.claude/agents/verifier.md` — system prompt loaded automatically via `subagent_type: "verifier"`.

## Agent Call

```
Agent({
  subagent_type: "verifier",
  description: "Verifier: validate {task_name}",
  model: "{verifier_model from .godotmaker/config.yaml, default: sonnet}",
  prompt: "{verifier brief below}"
})
```

## Verifier Brief Template

```
## Verify: {what is being checked}                      [REQUIRED]

### Project Path                                         [REQUIRED]
{Absolute path to the Godot project}

### Commands to Run (run ALL, do not skip)               [REQUIRED]
1. Build: godot --headless --quit 2>&1
2. Unit tests: godot --headless -s addons/gdunit4/bin/gdunit4_run.gd --single --file {test_file}
3. E2E test: {exact e2e run command — MUST actually run the game and exercise the feature}
4. {additional commands}

### E2E Verification (MANDATORY)                         [REQUIRED]
- Run the e2e test that the worker wrote
- Confirm it exercises the worker's feature (not just imports/compiles)
- Confirm the game does not crash during the e2e scenario
- If e2e test file is a placeholder (< 50 chars, contains "TODO"/"pass"): report FAIL
- Include e2e output (pass/fail count) in your report

### Success Criteria                                     [REQUIRED]
- [ ] Build: zero errors
- [ ] Unit tests: all pass
- [ ] E2E test: runs, exercises feature, no crash
- [ ] {additional specific criteria}

### Negative Tests                                       [OPTIONAL]
- [ ] {input that should fail and how}

### Focus Areas                                          [OPTIONAL]
{Specific files, systems, or interactions to stress-test}

### Visual Cross-Check                                     [REQUIRED for UI/scene tasks]
For tasks involving UI screens, HUD, menus, or scene layouts, verifier MUST perform
a three-way cross-check:

1. **SCENES.md description** — the specification (element names, positions, sizes)
2. **Reference image** at `references/scene_{name}.png` — the visual target
3. **Actual screenshot** — captured via `game.screenshot()` during e2e test

Verification criteria:
- [ ] All elements from SCENES.md description are present in the screenshot
- [ ] Element positions roughly match the description (top-left is top-left, not bottom-right)
- [ ] Element proportions roughly match (40%w element shouldn't be 10%w or 90%w)
- [ ] Overall visual style is consistent with reference image (color palette, mood)
- [ ] No major layout issues: overlapping elements, off-screen elements, unreadable text

This is NOT pixel-perfect comparison — it's a sanity check that the implementation
follows the design spec. Minor deviations are acceptable.
```

## Spot-Check Protocol

After EVERY verifier returns:
1. Read the verifier's full report
2. Pick 2-3 commands from the "Command run" sections
3. Re-run them yourself in Bash
4. Compare your output to the verifier's reported output
5. If outputs match: accept the report
6. If outputs differ: reject the report, note the discrepancy, re-dispatch verifier
7. For UI/scene tasks: compare the verifier's screenshot against SCENES.md and reference image yourself. Confirm the layout matches.
