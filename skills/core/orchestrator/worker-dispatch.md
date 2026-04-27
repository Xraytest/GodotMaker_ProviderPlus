# Worker Dispatch Protocol

When dispatching a worker, fill in this EXACT template. All REQUIRED fields must be present. OPTIONAL fields may be omitted.

**Agent definition:** `.claude/agents/worker.md` — system prompt loaded automatically via `subagent_type: "worker"`.

## Agent Call

```
Agent({
  subagent_type: "worker",
  description: "Worker: implement {task_name}",
  model: "{worker_model from .godotmaker/config.yaml, default: opus}",
  prompt: "{worker brief below}"
})
```

## Worker Brief Template

```
## Task: {name}                                         [REQUIRED]

### Objective                                            [REQUIRED]
{1-2 sentences: what to build and why it matters to the game}

### Context                                              [REQUIRED]
- Project: {game name and type}
- ECS Framework: gecs
- Project Path: {absolute path}

### Input Files (Read These First)                       [REQUIRED]
- {path}: {what it contains}

### Deliverables                                         [REQUIRED]
- [ ] {file path}: {what it should contain}
- [ ] {unit test file path}: {test scenarios — minimum 2 unit tests}
- [ ] e2e-testable interface: public methods / signals / simulate_* helpers exposed on this system, with unit tests covering each one
- [ ] Run headless-build and confirm compilation
- [ ] Run unit tests and include pass/fail output
- [ ] Summary of what was implemented (<200 words)
- [ ] MEMORY entry: discoveries, gotchas, decisions (<100 words)

### Component Definitions                                [REQUIRED]
{Paste the actual Component class definitions, not just names}

### Scope Boundaries                                     [REQUIRED]
- MUST: {explicit requirements}
- MUST NOT: {explicit prohibitions — always include "MUST NOT modify files outside Deliverables"}

### Gotchas                                              [REQUIRED for ECS tasks]
- MUST include: "Read .claude/skills/gecs/gotchas.md before writing any code"
- Copy relevant gotchas from reviewer skills (ui/gotchas.md, animation/gotchas.md, etc.)

### Prohibited Actions                                   [REQUIRED]
- DO NOT fabricate resource paths — only use paths listed in ASSETS.md or verified to exist in the project. If you need an asset that doesn't exist, report it in your summary; do NOT invent a path.
- DO NOT modify files outside your Deliverables list — read-only access to all other files.
- DO NOT write `test_system_has_query` tests — system.q is null outside World (see gecs gotcha G14).

### Assets Available                                     [OPTIONAL]
{Asset paths and descriptions}

### Scene Layout Reference                                [REQUIRED for UI/scene tasks]
{Copy the relevant scene description from SCENES.md here.
 Include: element positions, sizes, layout type, mood.
 Worker MUST follow these layout specs — element positions and proportions
 must match the description. Reference image at references/scene_{name}.png}
```

## Dispatch Rules

1. **Never delegate understanding.** Your brief must include specific file paths, Component fields, expected behavior. Not "implement movement based on the design."
2. **One objective per worker.** ONE system + its tests, or ONE scene, or ONE UI screen.
3. **Workers write their own tests.** Minimum 2 unit tests per system.
4. **Workers must not spawn sub-workers.**
5. **Include the WHY.** Workers who understand the game context make better decisions.
6. **MEMORY entry is mandatory.** Every worker reports what they learned.
7. **Test file naming**: `test_{source_file_stem}.gd` — e.g., system file `s_movement.gd` → test file `test_s_movement.gd`. check_project.py enforces this pattern.
8. **After creating files with `class_name`**: remind worker to run `godot --headless --import` to rebuild the cache.
9. **gdUnit4 version compatibility**: Godot 4.4 → gdUnit4 v5.x, Godot 4.5+ → gdUnit4 v6.x. Headless mode requires `--ignoreHeadlessMode`.
10. **E2E input handling**: do NOT use `Input.is_action_just_pressed()` in ECS systems. Use `_input()` callback + flag variable pattern, expose `simulate_*()` methods so the Evaluator's e2e tests can drive the system.
11. **UI scene root must be Control**: Any scene containing UI (menus, HUD, panels) must use a Control node as root, not Node2D. Control anchor/layout only works when the entire ancestor chain is Control nodes.
12. **Entity.name must be set explicitly**: When creating Entity instances programmatically, set `entity.name = "MyEntity"` before `add_entity()`. Without this, Godot assigns unpredictable auto-names (`@Node@2`), breaking E2E test node paths.
13. **Worker self-check is mandatory**: Workers must run the self-check protocol before submitting their report. If self-check is not mentioned in the report, reject it.
14. **UI/scene tasks require SCENES.md reference.** When dispatching a worker for any UI screen, HUD, menu, or scene layout task, you MUST copy the relevant scene description from SCENES.md into the brief. Workers without layout specs will produce inconsistent UIs.
15. **Worker model from config.** Read `worker_model` from `.godotmaker/config.yaml` (default: `opus`) and include it as `model:` in every Agent() call. See the Agent Call template at the top.

## Worker Utility Convention

Workers may create shared utility functions. Follow these rules:

1. **Location**: All utility/helper functions go in `src/utils/` directory.
2. **One file per domain**: e.g., `src/utils/math_utils.gd`, `src/utils/spawn_utils.gd`.
3. **After creating utilities**: Report them in your MEMORY entry so orchestrator can update the utils API doc.
4. **Before creating utilities**: Check `.godotmaker/utils_api.md` (if it exists) for existing utilities. Do NOT duplicate.
5. **Orchestrator responsibility**: After each worker completes, update `.godotmaker/utils_api.md` with new utility function signatures and descriptions. Include this doc path in subsequent worker briefs under "Input Files".

---

## Parallel Worker Dispatch (Worktree Isolation)

Workers with **no file ownership overlap** can run in parallel using git worktree isolation. This lets the orchestrator continue dispatching without waiting for each worker to finish.

### When to parallelize

- Two or more tasks have **completely disjoint file sets** (no shared .gd/.tscn/.tres files)
- Both tasks are in the same `/gm-build` cycle (risk or main phase)
- Neither task depends on the other's output

### How to dispatch

Use the Agent tool with `isolation: "worktree"` for each parallel worker:

```
Agent({
  subagent_type: "worker",
  description: "Worker: implement {system_A}",
  model: "{worker_model}",
  isolation: "worktree",
  prompt: "{worker brief A}"
})

Agent({
  subagent_type: "worker",
  description: "Worker: implement {system_B}",
  model: "{worker_model}",
  isolation: "worktree",
  prompt: "{worker brief B}"
})
```

Send **both Agent calls in the same message** — this is what triggers parallel execution.

### Merge procedure after parallel workers complete

Each worktree agent returns a branch name if it made changes. Merge them back:

1. **Check for conflicts** before merging:
   ```bash
   git diff main..{branch_A} --name-only
   git diff main..{branch_B} --name-only
   ```
   Verify no overlapping files. If overlap exists, merge sequentially and resolve conflicts.

2. **Merge each branch**:
   ```bash
   git merge {branch_A} --no-edit
   git merge {branch_B} --no-edit
   ```

3. **Run build after merge** to catch integration issues:
   ```bash
   godot --headless --quit 2>&1
   ```

4. **If merge conflict occurs**: resolve manually, prioritizing the more recent/complete implementation. Then re-run both workers' unit tests to confirm.

### Rules

- **Never parallelize workers that share files** — the merge will conflict
- **Shared read-only files are OK** — multiple workers can READ the same files
- **Verifiers/reviewers run sequentially** after merge — they need the combined project state
- **Max 3 parallel workers** at once — more than 3 increases merge complexity
- **Always build-check after merge** — parallel workers can't know about each other's changes
