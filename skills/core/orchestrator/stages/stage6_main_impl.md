# Stage 6: Main Implementation

Implement all Main Build tasks from PLAN.md. Follow build order from STRUCTURE.md.

**Implementation order:** Infrastructure first (Components, core Systems), then features.

For each task, run the **Implement -> Verify -> Next** loop defined in SKILL.md.

**File ownership for parallel workers:** No two concurrent workers may write to the same file. Verify BEFORE dispatching.

**Gate 6:**
- [ ] ALL tasks in PLAN.md are `completed`
- [ ] Run `python tools/check_project.py <project_dir> --all` — paste full output
- [ ] All checks pass (no FAIL lines)

**After passing Gate 6:** Update `.godotmaker/stage.json` — read existing (or create `{"completed_stages": {}}`), add `"6": "<UTC timestamp>"` to `completed_stages`, write back. Then proceed to Stage 7.
