# godot-e2e Testing Patterns and Best Practices

## Table of Contents

1. [Fixture Strategies](#fixture-strategies)
2. [Physics-Based Testing](#physics-based-testing)
3. [UI Testing](#ui-testing)
4. [State Verification](#state-verification)
5. [Scene Transition Testing](#scene-transition-testing)
6. [Screenshot on Failure](#screenshot-on-failure)
7. [Flaky Test Mitigation](#flaky-test-mitigation)
8. [Batch Operations for Performance](#batch-operations-for-performance)
9. [Debugging Tips](#debugging-tips)
10. [CI Configuration](#ci-configuration)
11. [Common Gotchas](#common-gotchas)

---

## Fixture Strategies

### Strategy 1: Scene Reload (default, recommended)

One Godot process per test module. Scene reloaded before each test.

```python
@pytest.fixture(scope="module")
def _game_process():
    with GodotE2E.launch(PROJECT_PATH, timeout=15.0) as game:
        game.wait_for_node("/root/Main", timeout=10.0)
        yield game

@pytest.fixture(scope="function")
def game(_game_process):
    _game_process.reload_scene()
    _game_process.wait_for_node("/root/Main", timeout=5.0)
    yield _game_process
```

**When to use**: Most tests. Resets scene tree, node properties, script variables.
**Limitation**: Global state (singletons, autoloads, static vars) persists between tests.

### Strategy 2: Fresh Process (maximum isolation)

```python
@pytest.fixture(scope="function")
def game_fresh():
    with GodotE2E.launch(PROJECT_PATH, timeout=15.0) as game:
        game.wait_for_node("/root/Main", timeout=10.0)
        yield game
```

**When to use**: Tests modifying global state, crash recovery tests.
**Cost**: ~2-5 seconds per test for Godot startup.

### Strategy 3: Shared Session (fastest)

```python
@pytest.fixture(scope="session")
def game_session():
    with GodotE2E.launch(PROJECT_PATH, timeout=15.0) as game:
        game.wait_for_node("/root/Main", timeout=10.0)
        yield game
```

**When to use**: Read-only tests, carefully ordered tests.
**Risk**: No reset between tests. A crash ends the session.

### Skip the main menu

Jump directly to the scene under test:

```python
@pytest.fixture(scope="module")
def _game_process():
    with GodotE2E.launch(PROJECT_PATH) as game:
        game.wait_for_node("/root", timeout=10.0)
        game.change_scene("res://levels/level1.tscn")
        game.wait_for_node("/root/Level1", timeout=5.0)
        yield game
```

### Reset to a specific scene in function fixture

```python
@pytest.fixture(scope="function")
def game(_game_process):
    current = _game_process.get_scene()
    if not current.endswith("menu.tscn"):
        _game_process.change_scene("res://menu.tscn")
    else:
        _game_process.reload_scene()
    _game_process.wait_for_node("/root/Menu", timeout=5.0)
    yield _game_process
```

---

## Physics-Based Testing

### Always use wait_physics_frames for movement

```python
def test_player_moves_right(game):
    initial_x = game.get_property("/root/Main/Player", "position:x")
    game.input_action("ui_right", True)
    game.wait_physics_frames(10)          # NOT wait_process_frames
    game.input_action("ui_right", False)
    new_x = game.get_property("/root/Main/Player", "position:x")
    assert new_x > initial_x
```

### When to use which wait

| Wait | Use for |
|------|---------|
| `wait_physics_frames` | CharacterBody2D movement, collision, RigidBody, `is_on_floor()` |
| `wait_process_frames` | Animation progress, UI transitions, `_process` logic |
| `wait_seconds` | Timed game events, cooldowns (game time, not wall time) |
| `wait_for_property` | Any state that will eventually change (preferred over frame counts) |

### Gravity / falling test

```python
def test_player_falls(game):
    initial_y = game.get_property("/root/Main/Player", "position:y")
    game.wait_physics_frames(30)
    new_y = game.get_property("/root/Main/Player", "position:y")
    assert new_y > initial_y  # Y increases downward in Godot
```

### Jump test

```python
def test_player_jumps(game):
    # Ensure on ground first
    game.wait_for_property("/root/Main/Player", "is_on_floor", True, timeout=3.0)
    initial_y = game.get_property("/root/Main/Player", "position:y")
    game.press_action("jump")
    game.wait_physics_frames(5)
    peak_y = game.get_property("/root/Main/Player", "position:y")
    assert peak_y < initial_y  # Y decreases upward
```

---

## UI Testing

### Click a node (recommended)

```python
def test_button_click(game):
    game.click_node("/root/Menu/StartButton")
    game.wait_for_node("/root/GameLevel", timeout=5.0)
```

### Verify label text after click

```python
def test_click_updates_label(game):
    game.click_node("/root/Menu/ClickButton")
    game.wait_process_frames(2)
    text = game.get_property("/root/Menu/StatusLabel", "text")
    assert "Clicked" in text
```

### Navigate between scenes via UI

```python
def test_navigate_to_detail_and_back(game):
    game.click_node("/root/Menu/NavigateButton")
    game.wait_for_node("/root/Detail", timeout=5.0)

    game.click_node("/root/Detail/BackButton")
    game.wait_for_node("/root/Menu", timeout=5.0)
    assert game.get_property("/root/Menu/TitleLabel", "text") == "Main Menu"
```

### Check visibility

```python
def test_pause_menu_visibility(game):
    assert game.get_property("/root/Main/PauseMenu", "visible") == False
    game.press_action("ui_cancel")
    game.wait_process_frames(5)
    assert game.get_property("/root/Main/PauseMenu", "visible") == True
```

---

## State Verification

### Prefer wait_for_property over polling

```python
# BAD: manual polling loop
for _ in range(100):
    game.wait_physics_frames(1)
    if game.get_property("/root/Main", "score") == 10:
        break
else:
    assert False, "Score never reached 10"

# GOOD: server-side polling (fast, no network round-trips per poll)
game.wait_for_property("/root/Main", "score", 10, timeout=5.0)
```

### Test coin collection via teleportation

```python
def test_coin_increases_score(game):
    initial_score = game.get_property("/root/Main", "score")
    coin_pos = game.get_property("/root/Main/Coin", "global_position")
    game.set_property("/root/Main/Player", "global_position", coin_pos)
    game.wait_for_property("/root/Main", "score", initial_score + 1, timeout=2.0)
```

### Test method call return values

```python
def test_increment_method(game):
    result = game.call("/root/Main", "increment")
    assert result == 1
    assert game.get_property("/root/Main", "counter") == 1
```

---

## Scene Transition Testing

### change_scene blocks until loaded

```python
def test_level_transition(game):
    game.change_scene("res://levels/level2.tscn")
    # change_scene already waits for the scene to load
    game.wait_for_node("/root/Level2", timeout=5.0)  # extra safety for child init
    name = game.get_property("/root/Level2", "level_name")
    assert name == "Level 2"
```

### reload resets state

```python
def test_reload_resets(game):
    game.call("/root/Main", "add_to_counter", [10])
    assert game.get_property("/root/Main", "counter") == 10

    game.reload_scene()
    game.wait_for_node("/root/Main", timeout=5.0)
    assert game.get_property("/root/Main", "counter") == 0
```

### Verify current scene

```python
scene = game.get_scene()
assert "level2.tscn" in scene
```

---

## Screenshot on Failure

### Automatic (built-in fixtures)

Both `game` and `game_fresh` built-in fixtures auto-capture screenshots on failure.
Saved to `test_output/<test_name>_failure.png`.

### Manual capture

```python
def test_visual_state(game):
    game.press_action("ui_accept")
    path = game.screenshot("/tmp/after_accept.png")
    assert os.path.isfile(path)
```

### CI artifact collection (GitHub Actions)

```yaml
- name: Upload failure screenshots
  if: failure()
  uses: actions/upload-artifact@v4
  with:
    name: e2e-failure-screenshots
    path: test_output/
```

---

## Flaky Test Mitigation

### Rule 1: State-based over time-based

```python
# FLAKY: frame count depends on machine
game.press_action("ui_accept")
game.wait_physics_frames(5)
assert game.get_property("/root/Main", "animation_done") == True

# STABLE: waits until condition met
game.press_action("ui_accept")
game.wait_for_property("/root/Main", "animation_done", True, timeout=5.0)
```

### Rule 2: Direction over exact values

```python
# FRAGILE: exact position varies per machine
assert game.get_property(player, "position:x") == 450.0

# ROBUST: direction is deterministic
assert new_x > initial_x
```

### Rule 3: Generous timeouts

```python
game.wait_for_node("/root/Main", timeout=10.0)    # 10s for initial load
game.wait_for_property("/root/Main", "ready", True, timeout=5.0)
```

### Rule 4: Expose game state as properties

Instead of inferring state from position, add script variables:
`is_on_ground`, `is_dead`, `current_level`, `is_paused`.

---

## Batch Operations for Performance

```python
# SLOW: 3 TCP round-trips
x = game.get_property(player, "position:x")
y = game.get_property(player, "position:y")
health = game.get_property(player, "health")

# FAST: 1 TCP round-trip
results = game.batch([
    ("get_property", {"path": player, "property": "position:x"}),
    ("get_property", {"path": player, "property": "position:y"}),
    ("get_property", {"path": player, "property": "health"}),
])
x, y, health = results
```

Only instant commands work in batch. Deferred (input, waits) return errors.

---

## Debugging Tips

### Enable server-side logging

```python
with GodotE2E.launch(path, extra_args=["--e2e-log"]) as game:
    ...
```

Logs every request/response on the Godot side:
```
[godot-e2e] << get_property (id=2)
[godot-e2e] >> {"id":2,"result":{"_t":"v2","x":400.0,"y":300.0}}
```

### Dump scene tree

```python
import json
tree = game.get_tree("/root", depth=3)
print(json.dumps(tree, indent=2))
```

### TimeoutError diagnosis

```python
try:
    game.wait_for_node("/root/Missing", timeout=2.0)
except TimeoutError as e:
    print("Scene tree at timeout:", json.dumps(e.scene_tree, indent=2))
```

### Interactive debugging

```bash
# Terminal 1: Start Godot in E2E mode
godot --path ./project -- --e2e --e2e-port=6008 --e2e-log

# Terminal 2: Connect from Python
python -c "
from godot_e2e import GodotE2E
game = GodotE2E.connect(port=6008)
print(game.get_tree('/root', depth=2))
game.close()
"
```

---

## CI Configuration

### Windows (GitHub Actions)

```yaml
- name: Install Godot
  shell: pwsh
  run: |
    Invoke-WebRequest -Uri "https://github.com/godotengine/godot-builds/releases/download/4.4-stable/Godot_v4.4-stable_win64.exe.zip" -OutFile godot.zip
    Expand-Archive godot.zip -DestinationPath C:\godot

- name: Run E2E tests
  run: godot-e2e tests/e2e/ -v --timeout=60
  env:
    GODOT_PATH: C:\godot\Godot_v4.4-stable_win64.exe
```

### Linux (GitHub Actions, Xvfb required)

```yaml
- name: Install Godot
  run: |
    wget -q https://github.com/godotengine/godot-builds/releases/download/4.4-stable/Godot_v4.4-stable_linux.x86_64.zip
    unzip -q Godot_v4.4-stable_linux.x86_64.zip
    sudo mv Godot_v4.4-stable_linux.x86_64 /usr/local/bin/godot

- name: Run E2E tests
  run: xvfb-run --auto-servernum godot-e2e tests/e2e/ -v --timeout=60
```

### macOS (GitHub Actions)

```yaml
- name: Run E2E tests
  run: godot-e2e tests/e2e/ -v --timeout=60
  env:
    GODOT_PATH: /Applications/Godot.app/Contents/MacOS/Godot
```

### CI tips

- Increase `timeout` in `GodotE2E.launch()` to 15s for CI (first launch is slow)
- Upload `test_output/` as artifact for failure screenshots
- Add `--timeout=60` to godot-e2e / pytest to catch frozen Godot
- On Linux: use `--rendering-driver opengl3` if Vulkan not available
- godot-e2e does NOT support `--headless` (Godot bug #73557)

---

## Game State Survival Patterns

Games with death, pause, or scene reload mechanics can break E2E tests. These patterns prevent the most common failures.

### Keep-alive: prevent game-over during tests

If the player can die from inaction (Flappy Bird, platformers), long `wait_seconds` or `wait_physics_frames` calls will kill the player and crash the test (scene reload breaks the TCP connection).

```python
def keep_alive(game, frames, action="flap", interval=15):
    """Wait N physics frames while periodically pressing an action to stay alive."""
    elapsed = 0
    while elapsed < frames:
        chunk = min(interval, frames - elapsed)
        game.wait_physics_frames(chunk)
        elapsed += chunk
        if elapsed < frames:
            game.press_action(action)

def test_pipe_spawning(game):
    # WRONG: game.wait_seconds(3.0)  — bird dies, scene reloads, connection lost
    # RIGHT: keep alive while waiting
    keep_alive(game, 120, action="flap", interval=10)
    # Now check pipe count
```

### Smart keep-alive: read game state to decide actions

```python
def smart_keep_alive(game, frames, player_path, action="flap"):
    """Keep alive by monitoring player position — don't flap into the ceiling."""
    for _ in range(frames):
        game.wait_physics_frames(1)
        y = game.get_property(player_path, "position:y")
        if y > 400:  # too low, about to hit ground
            game.press_action(action)
        # If y < 100, don't flap — too high
```

### Pause handling: avoid input_action deadlock

`input_action` internally waits 2 physics frames. If the action triggers a pause (setting `get_tree().paused = true`), physics frames stop, and `input_action` hangs forever.

```python
# WRONG: deadlocks if "pause" triggers get_tree().paused = true
game.input_action("pause", True)

# RIGHT: use call() to toggle pause via method
game.call("/root/Main", "toggle_pause")
game.wait_process_frames(2)  # process frames still run when paused

# RIGHT: if you must use input, set AutomationServer to always process
# (In your Godot project code):
# AutomationServer.process_mode = Node.PROCESS_MODE_ALWAYS
```

### Scene reload: avoid reload_current_scene in gameplay

If game-over calls `get_tree().reload_current_scene()`, the ECS autoload state may not reset properly, and the TCP connection may break.

**Mitigation in test code:**
```python
# Use change_scene instead of reload_scene to force a clean load
game.change_scene("res://main.tscn")
game.wait_for_node("/root/Main", timeout=5.0)
```

**Mitigation in game code (worker brief should specify):**
- Game over → show UI overlay, don't reload scene
- Restart → `change_scene_to_file()` instead of `reload_current_scene()`
- ECS: call `ECS.world.clear()` before scene transition

---

## Common Gotchas

### 1. press_action vs held input

`press_action("move_right")` only taps (press + release = ~4 physics frames).
For movement that needs sustained input, hold explicitly:

```python
game.input_action("move_right", True)   # hold down
game.wait_physics_frames(20)             # hold for 20 frames
game.input_action("move_right", False)  # release
```

### 2. input_action vs input_key

`input_action` does NOT drive `Input.get_axis()` / `Input.get_vector()`.
If CharacterBody2D code uses these, use `input_key` with the mapped scancode.

### 3. Signal timing with wait_for_signal

Signal listener registers when the command arrives. Signals emitted BEFORE
the command are missed. Use `wait_for_property` for state-change assertions.

### 4. Exact position assertions

Physics produces different results across machines. Assert direction or ranges:
```python
assert new_x > old_x  # direction
assert abs(pos.x - expected) < 5.0  # range
```

### 5. Global state leaking between tests

`reload_scene` does NOT reset autoload singletons. If tests modify global state,
use `game_fresh` fixture (fresh process per test).

### 6. --headless not supported

godot-e2e requires a display. On Linux CI, use `xvfb-run`. On Windows/macOS CI,
a desktop session is available by default.

### 7. Batch limitations

`batch()` only supports instant commands. Any deferred command (input, wait_*,
change_scene) in a batch returns an error entry.

### 8. Timeout vs game time

`wait_seconds(t)` waits game time (affected by `Engine.time_scale`).
All `timeout` parameters use wall-clock time (not affected by time_scale).
If game sets `time_scale=0.1`, `wait_seconds(5)` takes 50 real seconds,
but `timeout=5.0` still fires after 5 real seconds.
