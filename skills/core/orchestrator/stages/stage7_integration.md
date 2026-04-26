# Stage 7: Integration Verification

After all tasks complete, dispatch a Sonnet Verifier for full-project verification:

1. **Build:** `godot --headless --quit 2>&1` — zero ERROR lines
2. **Unit Tests:** full suite — `godot --headless -s addons/gdunit4/bin/gdunit4_run.gd`
3. **E2E Tests:** full suite — all e2e scenarios
4. **Lint:** `gdlint .` — no errors
5. **Static Check:** `python tools/check_project.py <project_dir> --all`
6. **Visual Cross-Check:** For each scene in SCENES.md, capture a screenshot and compare against the reference image + description. Use VQA skill for automated comparison if available.

**Spot-check** the verifier report — follow the **mandatory spot-check format** in SKILL.md.
Must include: build + unit test re-run + at least 1 E2E test re-run with screenshots.

**Gate 7:**
- [ ] Build: PASS
- [ ] Unit tests: PASS (total: N passed, 0 failed)
- [ ] E2E tests: PASS (all scenarios — must have actual run output with pass/fail counts. "placeholder", "TODO", "N/A", or empty files = **automatic FAIL**)
- [ ] Lint: PASS or WARN-only
- [ ] Static check: all PASS
- [ ] Spot-check: CONFIRMED (must include at least 1 E2E test re-run with screenshot)
- [ ] Visual cross-check: screenshots captured for key scenes, layout matches SCENES.md descriptions

**Gate 7 blockers — any of these means FAIL:**
- E2E test files that are empty, contain only imports, or have "placeholder" / "TODO" in their name or content
- Spot-check that only ran build without running any test
- Unit test or E2E results reported without actual command output

**On Gate 7 failure:**
1. Identify which system(s) caused the failure from verifier output
2. Dispatch a worker to fix the specific issue (Implement -> Verify -> Next loop)
3. After fix, re-run Stage 7 (full integration verification)
4. Max 3 fix-and-retry cycles. After 3: report remaining issues to user.

**After passing Gate 7:** Update `.godotmaker/stage.json` — read existing (or create `{"completed_stages": {}}`), add `"7": "<UTC timestamp>"` to `completed_stages`, write back. Then proceed to Stage 8.
