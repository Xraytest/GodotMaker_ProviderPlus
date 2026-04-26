---
name: screenshot
description: |
  Capture gameplay screenshots using godot-e2e for visual verification.
  Use when you need to: take a screenshot of the running game, capture
  multiple screenshots during an E2E scenario, generate reference.png,
  visually verify game state, or provide screenshots for VQA analysis.
  Triggers: "screenshot", "capture screenshot", "take screenshot",
  "reference.png", "visual capture", "screenshot the game".
---

# Screenshot — Gameplay Capture via godot-e2e

$ARGUMENTS

Capture screenshots from a running Godot game using godot-e2e's internal
viewport capture. Works headless, multi-monitor safe, no external tools needed.

## Quick Capture (single screenshot)

Write and run a Python script:

```python
# capture_screenshot.py
import os, sys
from godot_e2e import GodotE2E

project_path = sys.argv[1] if len(sys.argv) > 1 else "."
save_path = sys.argv[2] if len(sys.argv) > 2 else "screenshot.png"

with GodotE2E.launch(project_path, timeout=15.0) as game:
    game.wait_for_node("/root/Main", timeout=10.0)
    game.wait_seconds(1.0)  # let the game render a few frames
    result = game.screenshot(save_path=save_path)
    print(f"Screenshot saved: {result}")
```

Run: `python capture_screenshot.py <project_dir> <output_path>`

## Multi-Point Capture (E2E with screenshots)

For capturing multiple screenshots during a gameplay scenario:

```python
# capture_gameplay.py
import os, sys
from godot_e2e import GodotE2E

project_path = sys.argv[1] if len(sys.argv) > 1 else "."
output_dir = sys.argv[2] if len(sys.argv) > 2 else "screenshots"
os.makedirs(output_dir, exist_ok=True)

with GodotE2E.launch(project_path, timeout=15.0) as game:
    game.wait_for_node("/root/Main", timeout=10.0)

    # 1. Initial state
    game.wait_seconds(0.5)
    game.screenshot(save_path=os.path.join(output_dir, "01_initial.png"))

    # 2. After some interaction (customize per game)
    game.wait_seconds(2.0)
    game.screenshot(save_path=os.path.join(output_dir, "02_gameplay.png"))

    # 3. Later state
    game.wait_seconds(3.0)
    game.screenshot(save_path=os.path.join(output_dir, "03_later.png"))

    print(f"Captured {len(os.listdir(output_dir))} screenshots to {output_dir}/")
```

## Generate reference.png

Use the quick capture method, save to `reference.png` in the project root:

```bash
python capture_screenshot.py <project_dir> <project_dir>/reference.png
```

If the game has a title screen, wait for it to load and capture. If the game
starts directly in gameplay, capture after 1-2 seconds of gameplay.

## Spot-Check Screenshots

During spot-check, use multi-point capture with game interactions:

```python
# spot_check_capture.py
import os, sys
from godot_e2e import GodotE2E

project_path = sys.argv[1]
output_dir = os.path.join(project_path, "spot_check_screenshots")
os.makedirs(output_dir, exist_ok=True)

with GodotE2E.launch(project_path, timeout=15.0) as game:
    game.wait_for_node("/root/Main", timeout=10.0)

    # Capture at intervals
    for i in range(4):
        game.wait_seconds(1.5)
        path = os.path.join(output_dir, f"spot_{i+1}.png")
        game.screenshot(save_path=path)
        print(f"Spot-check screenshot {i+1}: {path}")
```

## API Reference

| Method | Description |
|--------|-------------|
| `game.screenshot(save_path="")` | Capture viewport as PNG. Returns absolute path. If `save_path` is empty, saves to a temp file. |

## Debug Collision Visualization

When capturing screenshots for physics/collision verification, launch Godot
with `--debug-collisions` to render collision shapes as visible overlays:

```python
with GodotE2E.launch(project_path, timeout=15.0,
                     extra_args=["--debug-collisions"]) as game:
    game.wait_seconds(1.0)
    game.screenshot(save_path="collision_check.png")
```

This makes CollisionShape2D/3D outlines visible in the capture, allowing
VQA to verify that collision bounds match sprite extents.

## Rules

1. **Always use `game.screenshot()`** — internal viewport capture. Do NOT use external screenshot tools.
2. **Wait before capturing** — `game.wait_seconds(0.5)` minimum after scene load to ensure rendering is complete.
3. **Save with descriptive names** — `01_initial.png`, `02_after_input.png`, not `screenshot1.png`.
4. **Orchestrator can write .py** — you are allowed to write Python capture scripts. You are only blocked from writing .gd/.tscn/.tres.
5. **Collision verification** — use `--debug-collisions` when verifying physics/collision correctness.
