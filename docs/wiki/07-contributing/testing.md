# Testing

GodotMaker uses pytest for all Python tests. The test suite covers hooks (pipeline enforcement) and tools (CLI utilities).

## Framework and Configuration

- **Framework**: pytest
- **Configuration**: `pyproject.toml` at the repository root
- **Python path**: `hooks/` is added to `pythonpath` so hook imports resolve correctly
- **Markers**: `network` for tests requiring network access (skip with `-m "not network"`)

## Test Structure

```
tests/
  __init__.py
  hooks/
    __init__.py
    helpers.py                   Shared test utilities
    test_check_completion.py     Completion criteria
    test_check_file_permissions.py   File permission checks
    test_check_stage_prerequisites.py  Stage prerequisites
    test_check_worker_report.py  Report format validation
    test_metrics.py              Metrics subsystem
    test_session_start.py        Session initialization
    test_stage_reminder.py       Stage reminder injection
  tools/
    __init__.py
    conftest.py                  Shared fixtures for tool tests
    test_addon_versions.py       Addon version mappings
    test_check_classname.py      Classname conflict detection
    test_check_env.py            Environment validation
    test_check_project.py        Project completeness
    test_publish.py              Publish/deploy logic
```

## Running Tests

Run the full suite (193 tests):

```bash
python -m pytest tests/ -x -q
```

Run a specific test file:

```bash
python -m pytest tests/hooks/test_check_worker_report.py -x -q
```

Run a specific test by name:

```bash
python -m pytest tests/ -k "test_blocks_missing_sections" -x -q
```

Run with verbose output:

```bash
python -m pytest tests/ -v
```

Skip network-dependent tests:

```bash
python -m pytest tests/ -m "not network" -x -q
```

## Test Helpers

The file `tests/hooks/helpers.py` provides four functions used across all hook tests:

### `run_hook(script_name, input_data)`

Spawns a hook script as a subprocess, sends JSON on stdin, and captures the result.

```python
from helpers import run_hook

stdout, exit_code, parsed = run_hook("check_file_permissions.py", {
    "event": "PreToolUse",
    "tool_name": "Write",
    "tool_input": {"file_path": "CLAUDE.md", "content": "..."}
})
```

**Parameters:**
- `script_name` -- Hook script filename (e.g., `"check_file_permissions.py"`)
- `input_data` -- Dictionary serialized as JSON to stdin

**Returns:**
- `stdout` -- Raw stdout text
- `exit_code` -- Process exit code
- `parsed` -- Parsed JSON from stdout, or `None` if parsing fails

The function locates hook scripts by navigating from `tests/hooks/` up to the repository root, then into `hooks/`. It sets a 10-second timeout and suppresses `.pyc` generation.

### `is_blocked(parsed)`

Checks if a hook response indicates a block decision. Supports two response formats:

```python
from helpers import is_blocked

# SubagentStop / Stop format
is_blocked({"decision": "block"})  # True

# PreToolUse format
is_blocked({"hookSpecificOutput": {"permissionDecision": "deny"}})  # True

is_blocked(None)  # False
```

### `write_stage_json(max_stage)`

Creates `.godotmaker/stage.json` with completed stages up to the given number. Used to set up stage prerequisites in tests.

```python
from helpers import write_stage_json

write_stage_json(5)  # Creates stage.json with stages 1-5 completed
```

### `cleanup_metrics()`

Removes the `.godotmaker/` directory and all metrics artifacts. Typically called in test teardown.

```python
from helpers import cleanup_metrics

cleanup_metrics()  # Deletes .godotmaker/ recursively
```

## Writing New Hook Tests

Hook tests follow a consistent pattern:

1. **Set up the environment** -- Create any required files (stage.json, metrics, etc.)
2. **Build event data** -- Construct the JSON input matching the hook's expected event format
3. **Call `run_hook`** -- Run the hook as a subprocess
4. **Assert the decision** -- Check if the hook allowed or blocked the action

Example test:

```python
import os
import pytest
from helpers import run_hook, is_blocked, write_stage_json, cleanup_metrics


class TestMyHook:
    def setup_method(self):
        write_stage_json(3)

    def teardown_method(self):
        cleanup_metrics()

    def test_allows_valid_input(self):
        event = {
            "event": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": "src/player.gd", "content": "extends Node"}
        }
        stdout, code, parsed = run_hook("check_file_permissions.py", event)
        assert not is_blocked(parsed)

    def test_blocks_protected_file(self):
        event = {
            "event": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": "CLAUDE.md", "content": "overwrite"}
        }
        stdout, code, parsed = run_hook("check_file_permissions.py", event)
        assert is_blocked(parsed)
```

Key points:
- Each test is self-contained with its own setup/teardown
- Use `write_stage_json` to control pipeline stage
- Use `cleanup_metrics` to avoid test pollution
- The `is_blocked` helper handles both response formats

## Writing New Tool Tests

Tool tests use standard pytest patterns. The `tests/tools/conftest.py` file provides shared fixtures.

```python
import pytest
from pathlib import Path


def test_my_tool_feature(tmp_path):
    """Test using pytest's tmp_path fixture for isolation."""
    # Create test files in tmp_path
    (tmp_path / "project.godot").write_text("[gd_resource]")

    # Import and call tool functions directly
    from tools.my_tool import my_function
    result = my_function(tmp_path)

    assert result == expected_value
```

Tool tests typically:
- Use `tmp_path` for filesystem isolation
- Import tool functions directly (no subprocess needed)
- Create minimal fixture files as needed

## Current Coverage

As of version 0.3.0, the test suite contains **193 tests**:

| Directory | Test Files | Focus |
|---|---|---|
| `tests/hooks/` | 7 test files + 1 helper | Hook behavior, metrics, stage validation |
| `tests/tools/` | 5 test files + 1 conftest | Publish, environment, project checks |
