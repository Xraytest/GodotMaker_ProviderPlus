# Asset Tools

GodotMaker includes several Python tools for generating and processing game assets.

## asset_gen.py -- Asset Generator CLI

Unified CLI for generating images, videos, and 3D models using AI backends.

### Subcommands

#### `image` -- Generate PNG images

```bash
python tools/asset_gen.py image --prompt "pixel art sword, 32x32" -o assets/sprites/sword.png
python tools/asset_gen.py image --prompt "edit: add glow" --image assets/sprites/sword.png -o assets/sprites/sword_glow.png
```

| Flag | Default | Description |
|---|---|---|
| `--prompt` | (required) | Image generation prompt |
| `--model` | `grok` | Backend: `grok` (fast) or `gemini` (precise) |
| `--size` | `1K` | Resolution (e.g., `1K`, `2K`, `4K`; see `--help`) |
| `--aspect-ratio` | `1:1` | Aspect ratio (many options; see `--help`) |
| `--image` | none | Reference image for image-to-image editing |
| `-o, --output` | (required) | Output PNG path |

#### `video` -- Generate MP4 video

```bash
python tools/asset_gen.py video --prompt "sword spinning" --image assets/sprites/sword.png --duration 3 -o assets/video/sword_spin.mp4
```

| Flag | Default | Description |
|---|---|---|
| `--prompt` | (required) | Video generation prompt |
| `--image` | (required) | Reference image (starting frame) |
| `--duration` | (required) | Duration in seconds (1-15) |
| `--resolution` | `720p` | `480p` or `720p` |
| `-o, --output` | (required) | Output MP4 path |

#### `glb` -- Convert PNG to 3D model

```bash
python tools/asset_gen.py glb --image assets/sprites/tree.png -o assets/models/tree.glb
```

| Flag | Default | Description |
|---|---|---|
| `--image` | (required) | Input PNG path |
| `--quality` | `default` | `default` or `high` |
| `-o, --output` | (required) | Output GLB path |

#### `set_budget` -- Set asset generation budget

```bash
python tools/asset_gen.py set_budget 500
```

Sets the budget cap in cents. Tracked via `assets/budget.json`. All generation commands check the remaining budget before proceeding and exit with an error if insufficient.

### Output Format

All subcommands print JSON to stdout:

```json
{"ok": true, "path": "assets/sprites/sword.png", "cost_cents": 2}
```

On failure:

```json
{"ok": false, "error": "Budget exceeded: need 15c but only 3c remaining", "cost_cents": 0}
```

### Required Environment Variables

| Variable | Required for |
|---|---|
| `GOOGLE_API_KEY` or `GEMINI_API_KEY` | `--model gemini` |
| `XAI_API_KEY` | `--model grok` and `video` |
| `TRIPO3D_API_KEY` | `glb` subcommand |

### Advanced

**Backend comparison:**

| Backend | Speed | Quality | Cost per image |
|---|---|---|---|
| Grok (xAI) | Fast | Good for most sprites | 2c flat (1K or 2K) |
| Gemini | Slower | More precise, better detail | 5c (512) / 7c (1K) / 10c (2K) / 15c (4K) |

**Video cost:** 5c per second.

**GLB quality modes:**

| Mode | Notes |
|---|---|
| `default` | Best low-poly, game-optimized topology. Cost: ~50c |
| `high` | HD textures, detailed geometry. Cost: ~40c |

---

## rembg_matting.py -- Background Removal

Removes solid-color backgrounds from images using color matting combined with BiRefNet neural network masks.

```bash
# Auto-detect best mode (recommended)
python tools/rembg_matting.py image.png

# Custom output path
python tools/rembg_matting.py image.png -o output.png

# Batch mode (all PNGs in a directory)
python tools/rembg_matting.py --batch frames/ -o output_frames/

# Generate QA preview
python tools/rembg_matting.py image.png --preview
```

### Requirements

- `rembg` package (`pip install rembg`)
- `numpy`, `pillow`
- Optional: `onnxruntime-gpu` + CUDA for GPU acceleration

### Advanced

By default the tool auto-selects the best processing mode. You can force a specific mode with `-m`:

| Mode | When to use |
|---|---|
| `trust` | Standard subjects with a clear background — the recommended mode for most sprites |
| `adapt` | Subject fills most of the frame or has colors similar to the background |
| `color` | Simple solid-color backgrounds where AI-based removal gives poor results |
| `auto` | Default; lets the tool pick the best mode automatically |

```bash
# Force a specific regime
python tools/rembg_matting.py image.png -m trust
```

---

## grid_slice.py -- Sprite Sheet Slicer

Slices a grid image into individual PNG frames.

```bash
python tools/grid_slice.py spritesheet.png -o frames/ --grid 4x4
python tools/grid_slice.py items.png -o items/ --grid 2x2 --names "sword,shield,potion,helm"
```

| Flag | Default | Description |
|---|---|---|
| `input` | (required) | Input grid image |
| `-o, --output` | (required) | Output directory |
| `--grid` | `2x2` | Grid layout as `ColsxRows` (e.g., `3x3`, `2x4`) |
| `--names` | none | Comma-separated names for output files (without `.png`). Default: `01`, `02`, etc. |

Output JSON:

```json
{"ok": true, "cells": 4, "cell_size": "32x32", "paths": ["frames/01.png", ...]}
```

---

## find_loop_frame.py -- Animation Loop Finder

Detects the best loop point in a sequence of animation frames by comparing frame similarity.

```bash
python tools/find_loop_frame.py frames/ --skip 10 --min-gap 5
```

| Flag | Default | Description |
|---|---|---|
| `frames_dir` | (required) | Directory containing numbered frame PNGs |
| `--skip` | `10` | Skip first N frames (avoid intro/transition) |
| `--min-gap` | `5` | Minimum frames between loop candidates |
| `--top` | `5` | Show top N candidates on stderr |

Strategy: Automatically detects the best loop point in an animation clip.

Output JSON:

```json
{"loop_frame": 54, "similarity": 0.9983, "window": 7, "total_frames": 73}
```

---

## check_classname.py -- Class Name Validator

Checks GDScript files for `class_name` declarations that conflict with Godot built-in names. Shadowing a built-in name causes hard-to-debug errors in the Godot editor and at runtime.

```bash
python tools/check_classname.py <project_dir>
python tools/check_classname.py <project_dir> --json
```

Scans all `.gd` files (excluding `addons/`, `.godot/`, `.claude/`, `.git/`) for `class_name` declarations and compares them against a comprehensive blacklist of Godot built-in class names, singletons, and core variant types.

Human-readable output:

```
[PASS] No class_name conflicts with Godot built-in names.
```

Or:

```
[FAIL] Found 2 class_name conflict(s):

  src/components/timer.gd: class_name 'Timer' conflicts with Godot built-in 'Timer'
  src/systems/world.gd: class_name 'World' conflicts with Godot built-in 'World'
```

JSON output (`--json`):

```json
{
  "conflicts": [
    {"file": "src/components/timer.gd", "class_name": "Timer", "conflicts_with": "Timer"}
  ],
  "clean": false
}
```

Exit codes: 0 = clean, 1 = conflicts found, 2 = invalid directory.
