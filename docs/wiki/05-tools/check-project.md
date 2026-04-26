# Project Checker

`check_project.py` validates that a GodotMaker-generated game project is complete and correctly structured. It checks ECS setup, test coverage, planning documents, e2e tests, build readiness, and MCP registration.

## Usage

```bash
# Run all checks
python tools/check_project.py <project_dir> --all

# Run specific check categories
python tools/check_project.py <project_dir> --build --ecs --tests

# If no flags are specified, all checks run by default
python tools/check_project.py <project_dir>
```

### Flags

| Flag | Category |
|---|---|
| `--build` | Build readiness (project.godot) |
| `--ecs` | ECS framework (gecs) setup |
| `--tests` | Unit test coverage (gdUnit4) |
| `--e2e` | End-to-end test setup (godot-e2e) |
| `--plan` | Planning documents (PLAN.md, STRUCTURE.md, etc.) |
| `--mcp` | MCP server registration |
| `--all` | Run all of the above |

## Checks Performed

### Build Readiness (`--build`)

- `project.godot` exists
- `project.godot` contains an `[application]` section

### ECS Setup (`--ecs`)

- `addons/gecs/` directory exists
- At least one `.gd` file extends `Component` or `GECSComponent`
- At least one `.gd` file extends `System` or `GECSSystem`

The checker scans all `.gd` files outside `addons/`, `.godot/`, and `.claude/` directories.

### Unit Tests (`--tests`)

- `addons/gdunit4/` directory exists
- Test files exist (files with "test" in their path)
- Each System file has a corresponding test file (matching `test_<name>`, `<name>_test`, or `test<name>` patterns)
- Reports which systems are missing test coverage

### E2E Tests (`--e2e`)

- godot-e2e plugin enabled in `project.godot`, or addon directory exists
- `tests/e2e/conftest.py` exists
- E2E test files found in `tests/e2e/` (matching `test_*.py`)
- Content quality: files must be >50 characters, contain `def test_` functions, and not consist entirely of placeholder content

### Planning Documents (`--plan`)

| File | Required | Checks |
|---|---|---|
| `PLAN.md` | Yes | Exists; has Task Status section with status markers (`pending`, `in_progress`, `completed`, etc.) |
| `STRUCTURE.md` | Yes | Exists; has Component Registry (Component + Registry/table); has System Schedule (System + Schedule) |
| `MEMORY.md` | No (warned) | Exists |
| `ASSETS.md` | No (warned) | Exists |

### MCP Registration (`--mcp`)

- `.mcp.json` exists
- `.mcp.json` contains a `"godot"` server entry

## Output Format

```
[PASS] project.godot exists
[FAIL] No System files found (files extending System)
[WARN] MEMORY.md not found (optional but recommended)
```

Summary at the end:

```
==================================================
Total: 18 checks
  PASS: 15
  FAIL: 2
  WARN: 1

Result: CHECKS FAILED
Failed checks:
  - No System files found (files extending System)
  - Systems without test files: movement_system, spawn_system
```

## Exit Codes

| Code | Meaning |
|---|---|
| 0 | All checks passed |
| 1 | One or more checks failed |
| 2 | Project directory does not exist |

## Integration with Hooks

The `check_completion` hook (triggered on Stop events) calls this tool to verify project completeness before allowing the orchestrator to finish.
