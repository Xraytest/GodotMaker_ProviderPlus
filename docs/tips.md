# Tips & Tricks

Non-obvious design decisions and implementation tricks in GodotMaker.
These exist to prevent future confusion when reading the code.

## Forced Self-Review on Stop (check_completion.py)

**What:** The first time the orchestrator tries to stop (Stop hook fires),
the hook unconditionally blocks — regardless of actual project state.

**Why:** In 3-game testing, orchestrators consistently "forgot" to verify
E2E test coverage and screenshot completeness before declaring done.
Prompt-level reminders were unreliable. A forced block guarantees the
orchestrator pauses to self-check at least once.

**How it works:**
1. `stop_block_count` starts at 0 in `.godotmaker/state.json`
2. First Stop (`block_count == 0`): always block, print current E2E/screenshot
   status, increment counter
3. Subsequent Stops (`block_count >= 1`): run normal checks (project completeness,
   diligence, E2E coverage)
4. Anti-deadloop (`block_count >= 5`): force-allow to prevent infinite retry

**The block message includes concrete status** (E2E run count, screenshot count,
SCENES.md scene count) so the orchestrator has actionable information, not just
a generic reminder.

## Git Worktree Requires Initial Commit (stage3_scaffold.md)

**What:** Stage 3 must create an initial git commit after scaffolding.

**Why:** Workers use `isolation: "worktree"` for parallel execution.
Git worktree requires at least one commit — without it:
```
fatal: not a valid object name: 'HEAD'
```
Push is NOT required, only a local commit.

**Discovered:** 3 failures across 3-game testing. Workaround was falling
back to sequential execution, but the root fix is simply committing first.

## AskUserQuestion for Confirmations (SKILL.md Hard Rule 6)

**What:** Orchestrator must use the AskUserQuestion tool (not plain text)
when it needs user input.

**Why:** Plain text questions are easy to miss or ignore. AskUserQuestion
creates a structured interaction that reliably pauses for user response.
Observed in other Claude Code skills (e.g., git-shit-done) as a consistent
pattern for reliable user interaction.
