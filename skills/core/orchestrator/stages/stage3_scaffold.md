# Stage 3: Scaffold

Invoke the project-scaffold skill (`.claude/skills/project-scaffold/SKILL.md`).

The scaffold MUST create:
- Git repository (`git init` if not already in a git repo — required for parallel worker worktree isolation)
- `.godotmaker/config.yaml` — verify exists (created by publish script)
- Godot project structure (project.godot)
- gecs addon installed and configured — version from `.claude/config/addon_versions.json`
- gdUnit4 addon installed — version from `.claude/config/addon_versions.json`
- godot-e2e addon installed (enable as plugin in Project Settings) — version from `.claude/config/addon_versions.json`
- Base Component definitions from STRUCTURE.md
- Empty System files with correct class signatures
- E2E test directory with conftest.py: `tests/e2e/conftest.py` (see template below)

**E2E conftest.py template** (create in `tests/e2e/conftest.py`):
```python
import pytest
import os
from godot_e2e import GodotE2E

GODOT_PROJECT = os.path.join(os.path.dirname(__file__), "..")

@pytest.fixture(scope="module")
def _game_process():
    with GodotE2E.launch(GODOT_PROJECT, timeout=15.0) as game:
        game.wait_for_node("/root/Main", timeout=10.0)
        yield game

@pytest.fixture(scope="function")
def game(_game_process):
    _game_process.reload_scene()
    _game_process.wait_for_node("/root/Main", timeout=5.0)
    yield _game_process
```
All E2E test files MUST go in `tests/e2e/` and use the `game` fixture from this conftest.py.

**Addon installation:** Read `.claude/config/addon_versions.json`, detect Godot version, download exact tags specified. See `project-scaffold/references/addons.md` for details. Do NOT guess versions or use latest.

**Output:** Working Godot project skeleton that compiles.

**Gate 3 — run `python tools/check_project.py <project_dir> --build --ecs` and paste full output:**
- [ ] Git repo initialized (`.git/` exists)
- [ ] `.godotmaker/config.yaml` exists with default settings
- [ ] project.godot exists
- [ ] gecs addon present (addons/gecs/)
- [ ] gdUnit4 addon present (addons/gdunit4/)
- [ ] godot-e2e present (plugin enabled in [editor_plugins])
- [ ] Headless build passes: `godot --headless --quit 2>&1` — no ERROR lines
- [ ] At least 1 Component file exists
- [ ] At least 1 System file exists (empty stubs are acceptable at this stage)
- [ ] `tests/e2e/conftest.py` exists with `GodotE2E` import

> `--tests` (unit test coverage per system) is intentionally NOT run at Gate 3 — systems are empty stubs at scaffold stage. Test coverage is first checked at Gate 5.

**Initial commit (required for worktree isolation):**

The publish script (`tools/publish.py`) creates an initial empty commit automatically. After scaffolding, verify a commit exists (`git log --oneline -1`). If not, create one:
```
git add -A && git commit -m "Stage 3: project scaffold"
```
Parallel workers use `isolation: "worktree"` which requires at least one commit. Without it: `fatal: not a valid object name: 'HEAD'`. Push is NOT required.

**After passing Gate 3:** Update `.godotmaker/stage.json` — read existing (or create `{"completed_stages": {}}`), add `"3": "<UTC timestamp>"` to `completed_stages`, write back. Then proceed to Stage 4.
