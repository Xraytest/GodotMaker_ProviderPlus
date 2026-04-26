# Stage 5: Risk Implementation

If PLAN.md has Risk Tasks, implement each in isolation before main build. If no risk tasks, skip to Stage 6.

For each risk task, run the **Implement -> Verify -> Next** loop defined in SKILL.md.

**Gate 5 — run `python tools/check_project.py <project_dir> --build --ecs --tests` and paste full output:**
- [ ] All risk tasks in PLAN.md are `completed` with passing verification
- [ ] At least 1 System file exists with implementation (not empty stub)
- [ ] Each System file has a corresponding unit test file (test_xxx.gd or xxx_test.gd)
- [ ] No FAIL lines in check_project.py output

> Note: `--tests` checks that every System file has a matching test file. This is the earliest gate where test coverage is required — scaffold (Gate 3) only creates empty system stubs so test checks are intentionally deferred to here.

**On failure:** Fix (up to 3 attempts per issue), then re-verify. After 3 failures, stop and report to user.

**After passing Gate 5:** Update `.godotmaker/stage.json` — read existing (or create `{"completed_stages": {}}`), add `"5": "<UTC timestamp>"` to `completed_stages`, write back. Then proceed to Stage 6.
