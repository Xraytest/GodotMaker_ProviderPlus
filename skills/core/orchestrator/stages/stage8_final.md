# Stage 8: Final Acceptance

1. **Capture screenshots** — read `.claude/skills/screenshot/SKILL.md` and use the multi-point capture pattern to take 3+ screenshots during gameplay
2. **Generate reference.png** if it doesn't exist — use the quick capture method from the screenshot skill
3. **Feed screenshots to VQA** skill (`.claude/skills/visual-qa/SKILL.md`) for analysis — compare against reference images from `references/scene_{name}.png` AND layout descriptions from SCENES.md
4. If runtime issues, escalate to MCP (`mcp-driver` skill) for live debugging
5. Present final status to user with screenshots

**Screenshot capture:** Use the screenshot skill (`.claude/skills/screenshot/SKILL.md`). You can write .py capture scripts directly — orchestrator is only blocked from .gd/.tscn/.tres.

**Final report to user must include:**
- What was built (systems, components, features)
- Test results (unit test count, e2e test count, pass/fail)
- Known limitations or TODOs
- How to run the game

**Gate 8:**
- [ ] Game runs without crash (confirmed by e2e — must have actual run output, NOT "placeholder" or "N/A")
- [ ] At least one gameplay screenshot captured via godot-e2e `game.screenshot()`
- [ ] Visual QA completed — if no user-provided reference.png, use the captured screenshot as reference.png and do basic VQA (not all-black, not all-white, expected UI elements visible)
- [ ] User informed of results with screenshots attached
- [ ] Key scenes match SCENES.md layout descriptions (elements present, positions correct, proportions reasonable)

**Gate 8 blockers — any of these means FAIL:**
- "N/A" or "placeholder" for any check item
- No screenshot captured (VQA cannot be skipped)
- Game crashes on launch or during e2e scenario

**On Gate 8 failure:**
1. Analyze VQA issues or runtime errors from screenshots/MCP output
2. Dispatch a worker to fix the specific visual/runtime issue
3. Re-run the worker's verifier + reviewer
4. Re-run Stage 8 checks (e2e + VQA)
5. Max 3 fix-and-retry cycles. After 3: report to user with screenshots showing the issue.

**Note:** The Stop hook (`check_completion.py`) runs `check_project.py --all` as a final safety net when you finish.
