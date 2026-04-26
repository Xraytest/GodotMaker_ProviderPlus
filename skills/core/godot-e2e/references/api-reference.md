# godot-e2e API Reference

Complete reference for all classes, methods, types, and exceptions.

## Table of Contents

1. [GodotE2E (main class)](#godote2e)
2. [Node Operations](#node-operations)
3. [Input Simulation](#input-simulation)
4. [High-Level Input Helpers](#high-level-input-helpers)
5. [Frame Synchronization](#frame-synchronization)
6. [Synchronization (wait_for_*)](#synchronization)
7. [Scene Management](#scene-management)
8. [Screenshot](#screenshot)
9. [Batch Operations](#batch-operations)
10. [Types](#types)
11. [Exceptions](#exceptions)
12. [GodotClient (low-level)](#godotclient)
13. [GodotLauncher](#godotlauncher)
14. [pytest Fixtures](#pytest-fixtures)
15. [Godot Addon Setup](#godot-addon-setup)

---

## GodotE2E

`from godot_e2e import GodotE2E`

### GodotE2E.launch()

```python
GodotE2E.launch(
    project_path: str,       # Path to dir containing project.godot
    godot_path: str = None,  # Godot executable path (auto-discovered if None)
    port: int = 0,           # TCP port (0 = auto-allocate free port)
    timeout: float = 10.0,   # Seconds to wait for connection
    extra_args: list = None  # Extra args forwarded to Godot process
) -> GodotE2E  # context manager
```

Launches Godot with `--e2e` flag, connects over TCP, completes handshake.
Use as context manager for automatic cleanup.

**Godot discovery order**: `godot_path` param > `GODOT_PATH` env var > PATH search
(`godot`, `godot4`, `Godot_v4`).

**Raises**: `FileNotFoundError` (no Godot), `RuntimeError` (Godot exits early),
`ConnectionError` (timeout).

```python
with GodotE2E.launch("./my_project", timeout=15.0) as game:
    game.wait_for_node("/root/Main", timeout=10.0)
    # ... tests ...
# Godot process killed automatically
```

### GodotE2E.connect()

```python
GodotE2E.connect(
    host: str = "127.0.0.1",
    port: int = 6008,
    token: str = ""
) -> GodotE2E
```

Connect to an already-running Godot instance (started manually with `--e2e`).
If token was set via `--e2e-token`, it must match.

```python
# Start Godot manually: godot --path ./project -- --e2e --e2e-port=6008
game = GodotE2E.connect(port=6008)
```

### close()

Terminate the Godot process (if launched) and close TCP connection.
Called automatically by context manager.

---

## Node Operations

### node_exists(path) -> bool

Check if a node exists in the scene tree.

```python
game.node_exists("/root/Main/Player")  # True or False
```

### get_property(path, property) -> value

Get a node property. Supports Godot's colon-separated sub-property notation.

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | `str` | Absolute node path: `"/root/Main/Player"` |
| `property` | `str` | Property name. Use `:` for sub-properties: `"position:x"` |

**Returns**: Deserialized Python value (float, str, Vector2, etc.).

**Raises**: `NodeNotFoundError`, `CommandError` (property doesn't exist).

```python
pos = game.get_property("/root/Main/Player", "position")       # Vector2
x = game.get_property("/root/Main/Player", "position:x")       # float
text = game.get_property("/root/Main/Label", "text")            # str
visible = game.get_property("/root/Main/Menu", "visible")       # bool
health = game.get_property("/root/Main/Player", "health")       # int
```

### set_property(path, property, value)

Set a property on a node. Use godot-e2e type classes for Godot types.

```python
from godot_e2e import Vector2

game.set_property("/root/Main/Player", "position", Vector2(100.0, 200.0))
game.set_property("/root/Main/Player", "position:x", 500.0)
game.set_property("/root/Main", "score", 0)
game.set_property("/root/Main/Label", "text", "Hello")
```

### call(path, method, args=None) -> value

Call a GDScript method on a node.

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | `str` | Node path |
| `method` | `str` | Method name |
| `args` | `list` | Arguments list (each is serialized) |

```python
result = game.call("/root/Main", "get_counter")           # No args
game.call("/root/Main", "add_to_counter", [5])             # With args
game.call("/root/Main", "reset_level", [True, 3])          # Multiple args
```

### find_by_group(group) -> list[str]

Find all nodes in a Godot group. Returns list of absolute path strings.

```python
enemies = game.find_by_group("enemies")
# ["/root/Main/Enemy1", "/root/Main/Enemy2"]

players = game.find_by_group("player")
player_path = players[0]  # "/root/Main/Player"
health = game.get_property(player_path, "health")
```

### query_nodes(pattern="", group="") -> list[str]

Query nodes by glob pattern (`*`, `?` wildcards), group, or both.

```python
game.query_nodes(pattern="Enemy*")                    # All nodes named Enemy*
game.query_nodes(group="enemies")                     # All in "enemies" group
game.query_nodes(pattern="Boss*", group="enemies")    # Bosses in enemies group
```

### get_tree(path="/root", depth=4) -> dict

Scene tree snapshot as nested dict. Keys: `name`, `type`, `path`, `children`.

```python
tree = game.get_tree("/root/Main", depth=2)
# {"name": "Main", "type": "Node2D", "path": "/root/Main",
#  "children": [
#    {"name": "Player", "type": "CharacterBody2D", ...},
#    {"name": "Label", "type": "Label", ...}
#  ]}
```

---

## Input Simulation

All input commands are **deferred**: the server injects the input event, waits
2 physics frames for Godot to process it, then responds.

### input_action(action_name, pressed, strength=1.0)

Simulate a named input action (defined in Godot's Input Map).

**Most reliable method** — focus-independent. Use for all gameplay actions.

**Limitation**: Does NOT drive `Input.get_axis()` / `Input.get_vector()`. If game
code uses these, use `input_key()` instead.

```python
game.input_action("ui_right", True)    # press
game.input_action("ui_right", False)   # release
game.input_action("jump", True, strength=0.5)  # partial strength
```

### input_key(keycode, pressed, physical=False)

Simulate a keyboard key event. Goes through Godot's full input pipeline
(`_input`, `_unhandled_input`, action mapping). **DOES drive `Input.get_axis()`**.

| Parameter | Type | Description |
|-----------|------|-------------|
| `keycode` | `int` | Godot key constant (e.g., `4194321` = KEY_RIGHT) |
| `pressed` | `bool` | True for key-down, False for key-up |
| `physical` | `bool` | If True, sets physical_keycode (layout-independent) |

Common Godot keycodes (decimal):
- KEY_LEFT: 4194319, KEY_RIGHT: 4194321, KEY_UP: 4194320, KEY_DOWN: 4194322
- KEY_SPACE: 32, KEY_ENTER: 4194309, KEY_ESCAPE: 4194305
- KEY_A: 65, KEY_D: 68, KEY_W: 87, KEY_S: 83

### input_mouse_button(x, y, button=1, pressed=True)

Mouse button at screen coordinates. Button: 1=left, 2=right, 3=middle.

### input_mouse_motion(x, y, relative_x=0, relative_y=0)

Mouse motion event at screen position with optional relative movement.

---

## High-Level Input Helpers

Convenience wrappers that handle press + release automatically.

### press_action(action_name, strength=1.0)

Press and immediately release a named action. Equivalent to:
`input_action(action, True)` then `input_action(action, False)`.
Total wait: 4 physics frames (2 per input_action call).

**Use for taps/clicks, NOT for held movement.** For held input, use
`input_action(name, True)` → `wait_physics_frames(N)` → `input_action(name, False)`.

### press_key(keycode)

Press and release a key. Equivalent to two `input_key` calls.

### click(x, y, button=1)

Click at screen coordinates. Mouse down + wait + mouse up.

### click_node(path)

Click at a node's screen position. The server computes coordinates:
- **Control nodes**: center of `get_global_rect()`
- **Node2D nodes**: viewport-transformed global position

```python
game.click_node("/root/Menu/StartButton")  # Click the button
```

**Raises**: `NodeNotFoundError`, `CommandError` (unsupported node type).

---

## Frame Synchronization

### wait_process_frames(count=1)

Wait N `_process` (render) frames. Use for UI animations, `_process` logic.

### wait_physics_frames(count=1)

Wait N `_physics_process` frames. **Use for movement, collision, physics.**

### wait_seconds(seconds)

Wait N in-game seconds. Affected by `Engine.time_scale`.
Timeout parameters use wall-clock time (NOT affected by time_scale).

---

## Synchronization

### wait_for_node(path, timeout=5.0)

Block until node exists. Polls every process frame on the Godot side (fast).

**Raises**: `TimeoutError` with `.scene_tree` attribute containing a tree dump.

```python
game.wait_for_node("/root/Level2", timeout=10.0)
```

### wait_for_signal(path, signal_name, timeout=5.0)

Wait for a signal to emit. Returns list of signal arguments.

**IMPORTANT**: Only catches signals emitted AFTER the command is received.
For state changes triggered by actions, prefer `wait_for_property`.

```python
args = game.wait_for_signal("/root/Main", "level_complete", timeout=10.0)
```

### wait_for_property(path, property, value, timeout=5.0)

Poll until property equals expected value. Polls on Godot side (fast, no
network round-trips per poll).

```python
game.wait_for_property("/root/Main", "score", 10, timeout=5.0)
game.wait_for_property("/root/Main/Player", "is_on_floor", True, timeout=3.0)
```

---

## Scene Management

### get_scene() -> str

Returns current scene's `res://` path.

### change_scene(scene_path)

Change to a new scene. **Blocks until new scene is loaded and ready.**

```python
game.change_scene("res://levels/level2.tscn")
# No need for wait_for_node — change_scene already waits
```

### reload_scene()

Reload the current scene. **Blocks until reloaded.** Primary test isolation
mechanism — resets all scene state.

---

## Screenshot

### screenshot(save_path="") -> str

Capture viewport to PNG. Returns absolute file path.

If `save_path` is empty, saves to `user://e2e_screenshots/<timestamp>.png`.

The built-in pytest fixtures auto-capture on test failure to `test_output/`.

---

## Batch Operations

### batch(commands) -> list

Execute multiple **instant** commands in one TCP round-trip.

Each command is either a dict with `"action"` key, or a tuple of
`(action, params_dict)`.

**Deferred commands (input, waits) are NOT supported in batch** — they return
an error entry.

```python
results = game.batch([
    ("get_property", {"path": "/root/Main/Player", "property": "position:x"}),
    ("get_property", {"path": "/root/Main/Player", "property": "position:y"}),
    ("get_property", {"path": "/root/Main", "property": "score"}),
    {"action": "node_exists", "path": "/root/Main/Enemy"},
])
x, y, score, enemy_exists = results
```

---

## Types

`from godot_e2e import Vector2, Vector2i, Vector3, Vector3i, Rect2, Rect2i, Color, Transform2D, NodePath`

All are Python dataclasses mirroring Godot types. Used for `set_property` values
and returned by `get_property`.

| Type | Fields |
|------|--------|
| `Vector2(x, y)` | `float, float` |
| `Vector2i(x, y)` | `int, int` |
| `Vector3(x, y, z)` | `float, float, float` |
| `Vector3i(x, y, z)` | `int, int, int` |
| `Rect2(x, y, w, h)` | `float, float, float, float` |
| `Rect2i(x, y, w, h)` | `int, int, int, int` |
| `Color(r, g, b, a=1.0)` | `float, float, float, float` |
| `Transform2D(x, y, origin)` | `Vector2, Vector2, Vector2` |
| `NodePath(path)` | `str` |

Wire protocol uses `_t` type tags for lossless JSON round-trip.
Unsupported Godot types become `{"_t": "_unknown", "_class": "...", "_str": "..."}`.

---

## Exceptions

All inherit from `GodotE2EError`.

```python
from godot_e2e import (
    GodotE2EError,
    NodeNotFoundError,
    TimeoutError,
    ConnectionLostError,
    CommandError,
)
```

### NodeNotFoundError

Node path doesn't exist in scene tree.
Raised by: `get_property`, `set_property`, `call`, `click_node`, `wait_for_signal`.

### TimeoutError

Wait operation exceeded timeout. Has `.scene_tree` attribute (dict or None)
with a tree dump captured at timeout.

```python
try:
    game.wait_for_node("/root/Missing", timeout=2.0)
except TimeoutError as e:
    print(e.scene_tree)  # Shows what nodes DO exist
```

### ConnectionLostError

Godot process crashed or TCP connection dropped. Raised by any command.

### CommandError

Server returned an error (unknown command, bad property, failed method call).

---

## GodotClient

`from godot_e2e import GodotClient`

Low-level TCP client. You normally use `GodotE2E` instead.

- `GodotClient(host, port)` — constructor
- `connect(timeout=10.0)` — open TCP connection
- `close()` — close connection
- `hello(token)` — send handshake
- `send_command(action, **params)` — send command and block for response

---

## GodotLauncher

`from godot_e2e import GodotLauncher`

Process manager. Used internally by `GodotE2E.launch()`.

- `launch(project_path, godot_path, port, timeout, extra_args)` — start Godot, return connected client
- `kill()` — gracefully shut down Godot (quit command → terminate → kill)

The launcher:
1. Finds Godot binary
2. If `port=0` (default), creates a temporary port file and passes
   `--e2e-port=0 --e2e-port-file=<path>` so Godot auto-selects a free port
   and writes it to the file. This avoids TOCTOU race conditions and enables
   multiple parallel instances.
3. Generates random authentication token
4. Starts Godot with `--e2e`, `--e2e-port=N`, `--e2e-token=X`
   (and `--e2e-port-file` when auto-allocating)
5. Reads actual port from port file (if auto-allocated), then polls until
   TCP connection + handshake succeeds

---

## pytest Fixtures

The `godot_e2e.fixtures` module registers as a pytest plugin via `pytest11` entry point.

### Built-in `game` fixture (function scope)

Backed by a module-scoped Godot process. Reloads scene before each test.
Auto-captures screenshot on test failure to `test_output/<test_name>_failure.png`.

Project path resolution order:
1. `@pytest.mark.godot_project("path")` marker
2. `godot_e2e_project_path` in pytest config
3. `GODOT_E2E_PROJECT_PATH` env var
4. Auto-detection of `project.godot` in `./godot_project`, `../godot_project`, `.`

### Built-in `game_fresh` fixture (function scope)

Fresh Godot process per test. Maximum isolation, slowest. Auto-screenshots on failure.

### Custom fixtures (recommended)

Write your own `conftest.py` for full control:

```python
import pytest
import os
from godot_e2e import GodotE2E

GODOT_PROJECT = os.path.join(os.path.dirname(__file__), "..", "godot_project")

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

---

## Godot Addon Setup

### Files to copy

Copy `addons/godot_e2e/` into your Godot project. It contains:

| File | Purpose |
|------|---------|
| `plugin.gd` | EditorPlugin: auto-registers AutomationServer autoload |
| `plugin.cfg` | Addon metadata |
| `automation_server.gd` | Autoload: TCP server + state machine |
| `command_handler.gd` | Command dispatch + execution |
| `json_serializer.gd` | GDScript <-> JSON type conversion |
| `config.gd` | CLI flag parser (`--e2e`, `--e2e-port`, etc.) |

### Plugin registration

Enable in **Project > Project Settings > Plugins** — check the **GodotE2E** entry.
The plugin automatically adds `AutomationServer` as an autoload.

### CLI flags (passed after `--` separator)

| Flag | Description |
|------|-------------|
| `--e2e` | Enable automation server. Required. |
| `--e2e-port=N` | TCP port (default: 6008). Use `0` for auto-selection. |
| `--e2e-port-file=PATH` | Write actual port to this file. Used with `--e2e-port=0` for parallel instances. |
| `--e2e-token=X` | Auth token (must match client). |
| `--e2e-log` | Verbose server-side logging to stdout. |

The launcher passes these automatically. For manual launch:
```bash
godot --path ./project -- --e2e --e2e-port=6008 --e2e-log
```

### Zero production impact

The AutomationServer checks `--e2e` in `_ready()`. Without it:
- No TCP server is created
- `set_process(false)` + `set_physics_process(false)`
- Zero runtime overhead
