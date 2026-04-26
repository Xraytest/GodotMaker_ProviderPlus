---
name: godot-e2e
description: |
  Write and run E2E (end-to-end) game tests using the godot-e2e framework.
  godot-e2e is an out-of-process testing tool: Python controls a live Godot
  game over TCP — simulating input, reading game state, and asserting results.

  Use this skill whenever you need to:
  - Test actual gameplay: player movement, collisions, scoring, scene transitions
  - Verify UI interactions: button clicks, label text, menu navigation
  - Write integration tests that run the real game (not mocked unit tests)
  - Debug E2E test failures or set up E2E test infrastructure

  Triggers: "E2E test", "end-to-end test", "gameplay test", "test the game running",
  "simulate input", "test player movement", "test UI clicks", "godot-e2e",
  "integration test for game", "test scene transitions".
---

# godot-e2e — E2E Testing for Godot

$ARGUMENTS

godot-e2e is a custom framework with **zero LLM training data coverage**. Everything
the model needs is in this skill. Do not guess — follow these docs exactly.

## Architecture

The `godot-e2e` CLI launches a Godot process and communicates over TCP (localhost).
An Autoload node (`AutomationServer`) receives JSON commands, executes them on the
main thread, and sends back results. The game runs unmodified — the server is dormant
unless launched with `--e2e`. Multiple instances can run in parallel (each auto-allocates
a unique port).

## Quick Start — conftest.py + Test File

```python
# conftest.py (required per test directory)
import pytest, os
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

```python
# test_player.py
def test_player_moves_right(game):
    initial_x = game.get_property("/root/Main/Player", "position:x")
    game.input_action("ui_right", True)       # press
    game.wait_physics_frames(10)               # let physics run
    game.input_action("ui_right", False)       # release
    new_x = game.get_property("/root/Main/Player", "position:x")
    assert new_x > initial_x
```

```bash
godot-e2e e2e/ -v
```

## API Quick Reference

### Launch / Lifecycle

| Method | Description |
|---|---|
| `GodotE2E.launch(project_path, godot_path=None, port=0, timeout=10.0, extra_args=None)` | Context manager. Launch Godot + connect. `port=0` auto-allocates. |
| `GodotE2E.connect(host="127.0.0.1", port=6008, token="")` | Connect to already-running Godot. |
| `game.close()` | Kill Godot process and close connection. |

### Node Operations

| Method | Returns | Description |
|---|---|---|
| `game.node_exists(path)` | `bool` | Check if node exists in scene tree. |
| `game.get_property(path, prop)` | value | Get property. Use `"position:x"` for sub-properties. |
| `game.set_property(path, prop, value)` | — | Set property. Use godot-e2e types for Vector2 etc. |
| `game.call(path, method, args=None)` | value | Call method on node. `args` is a list. |
| `game.find_by_group(group)` | `[str]` | Find all nodes in a group (returns paths). |
| `game.get_tree(path="/root", depth=4)` | `dict` | Scene tree snapshot (for debugging). |
| `game.batch(commands)` | `[value]` | Multiple commands in one TCP round-trip (instant only). |

### Input Simulation

All input commands wait **2 physics frames** before returning.

| Method | Description |
|---|---|
| `game.input_action(action, pressed, strength=1.0)` | Named input action (2 args required). |
| `game.press_action(action)` | Press + release (convenience tap). |
| `game.input_key(keycode, pressed, physical=False)` | Keyboard key. Needed for `Input.get_axis()`. |
| `game.click_node(path)` | Click at node's screen position. |
| `game.click(x, y, button=1)` | Click at screen coords. |

### Frame Synchronization

| Method | Description |
|---|---|
| `game.wait_physics_frames(n)` | Wait N `_physics_process` frames. **Use for movement/physics.** |
| `game.wait_process_frames(n)` | Wait N `_process` frames. Use for UI/animation. |
| `game.wait_seconds(t)` | Wait t in-game seconds (affected by time_scale). |
| `game.wait_for_node(path, timeout=5.0)` | Block until node exists. Raises `TimeoutError`. |
| `game.wait_for_signal(path, signal_name, timeout=5.0)` | Block until signal emits. |
| `game.wait_for_property(path, prop, value, timeout=5.0)` | Block until property equals value. **Preferred over frame counting.** |

### Scene Management

| Method | Description |
|---|---|
| `game.get_scene()` | Get current scene `res://` path. |
| `game.change_scene(scene_path)` | Change scene (blocks until loaded). |
| `game.reload_scene()` | Reload current scene (blocks until ready). |
| `game.screenshot(save_path="")` | Capture viewport PNG. Returns absolute path. |

### Types & Exceptions

```python
from godot_e2e import Vector2, Vector2i, Vector3, Color, Rect2
```

| Exception | When |
|---|---|
| `NodeNotFoundError` | Node path doesn't exist. |
| `TimeoutError` | `wait_for_*` exceeded timeout. Has `.scene_tree` attribute. |
| `ConnectionLostError` | Godot process crashed or TCP dropped. |

## Critical Rules

| # | Rule | Detail |
|---|------|--------|
| 1 | **Physics frames for movement** | After input, use `wait_physics_frames` for position/collision assertions. `wait_process_frames` does NOT advance physics. |
| 2 | **Hold input for movement** | `press_action` only taps (~4 frames). For sustained movement: `input_action(act, True)` → `wait_physics_frames(N)` → `input_action(act, False)`. |
| 3 | **`input_action` needs 2 args** | `input_action("jump", True)` not `input_action("jump")`. For tap, use `press_action("jump")`. |
| 4 | **Prefer `wait_for_property`** | Frame counts are machine-dependent and flaky. Use `wait_for_property(path, prop, value, timeout)` instead. |
| 5 | **Assert direction, not exact values** | `assert new_x > initial_x` not `assert pos_x == 450.0`. Physics varies per machine. |
| 6 | **`wait_for_signal` timing** | Listener registers on arrival — signals emitted before are missed. Use `wait_for_property` for state assertions. |
| 7 | **Groups over hardcoded paths** | `game.find_by_group("player")[0]` is robust. `/root/Main/World/Player` breaks if tree changes. |

## Fixture Strategies

| Strategy | Scope | Speed | Isolation | Use when |
|---|---|---|---|---|
| `reload_scene` | module process + function reload | Fast | Good | Default. Most tests. |
| `game_fresh` | function process | Slow | Maximum | Tests that modify global/autoload state. |
| `session` | session process | Fastest | None | Read-only tests, careful ordering. |

## Running & Debugging

```bash
godot-e2e e2e/ -v                          # all tests
godot-e2e e2e/test_player.py -v             # single file
godot-e2e --godot-path /path/to/godot tests/ -v   # specific binary
```

- **Server logging**: `GodotE2E.launch(path, extra_args=["--e2e-log"])`
- **Dump scene tree**: `game.get_tree("/root", depth=3)`
- **TimeoutError diagnosis**: exception has `.scene_tree` attribute

## E2E Test Quality Standards

Every E2E test MUST meet these minimum requirements. Tests that fail these criteria are rejected.

### Minimum Per-Test Requirements

1. **At least 1 user action** — `input_action`, `press_action`, `click`, `click_node`, or `call` that triggers gameplay
2. **At least 1 state-change assertion** — verify a property CHANGED (not just that a node exists)
3. **No pure `node_exists` tests** — `node_exists` may be used as a precondition, but NEVER as the only assertion

### Bad vs Good Examples

```python
# BAD — only checks existence, proves nothing about gameplay:
def test_player(game):
    assert game.node_exists("/root/Main/Player")

# GOOD — verifies actual gameplay behavior:
def test_player_moves_right(game):
    initial_x = game.get_property("/root/Main/Player", "position:x")
    game.input_action("move_right", True)
    game.wait_physics_frames(10)
    game.input_action("move_right", False)
    assert game.get_property("/root/Main/Player", "position:x") > initial_x
```

### Orchestrator E2E Spec

Before dispatching a worker, the orchestrator writes an E2E spec to `.godotmaker/workers/{task_id}.md` containing:
- Task objective and constraints
- **E2E acceptance criteria**: specific "user action → expected state change" pairs
- Known gotchas or dependencies
- This file is passed to both the worker (for test writing) AND the verifier (for validation)

Verifiers MUST read the spec and confirm the worker's E2E tests cover ALL listed acceptance criteria.

## E2E Helper Convention

Workers maintain reusable E2E helper functions in `e2e/helpers/` to prevent test duplication and ensure fixture updates propagate.

1. Each worker creates/updates a helper file for their system's E2E interface (e.g., `player_helper.py`)
2. Helper functions wrap common multi-step operations (e.g., `start_game` = change scene + wait + verify)
3. Each helper file MUST have a corresponding unittest: `e2e/helpers/test_{name}_helper.py`
4. Helper unittests verify the helper functions work (game launches, actions execute, no crash)
5. When a worker modifies a system that changes E2E behavior (node paths, method signatures), they MUST update the corresponding helper

## Fixture Sync Rules

1. **Entry scene change** → update `conftest.py`: change `wait_for_node` path, add `change_scene` if needed
2. **Entity naming change** → update helpers that reference old entity paths
3. **New game state** (e.g., menu before gameplay) → create a `game_playing` fixture that navigates past menus to gameplay state
4. **Private → public methods** → E2E `game.call()` cannot call `_private()` methods; any method called by E2E must be public
5. **After ANY structural change** → run `godot-e2e e2e/ -v` to catch broken fixtures immediately

> **Note:** Orchestrator writes E2E specs to `.godotmaker/workers/{task_id}.md` before dispatching workers. Verifiers MUST confirm the worker's E2E tests cover ALL listed acceptance criteria.

## Extended References

For full API details (all parameters, return types, edge cases):
→ Grep `references/api-reference.md`

For testing patterns (keep-alive, pause handling, CI config, flaky test mitigation):
→ Grep `references/testing-patterns.md`
