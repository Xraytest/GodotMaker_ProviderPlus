# Godot Capture

All screenshot and frame sequence capture uses godot-e2e's internal Viewport capture.
This works headless, is multi-monitor safe, and does not require window focus.

See `.claude/skills/godot-e2e/SKILL.md` for full API reference.

## Single Screenshot

```python
game.screenshot("screenshots/current.png")
```

Captures the current Viewport and saves to the specified path.

## Frame Sequence (for VQA Dynamic Mode)

Capture frames at regular intervals for motion/animation analysis:

```python
frames = []
for i in range(6):
    path = f"screenshots/frame_{i:03d}.png"
    game.screenshot(path)
    frames.append(path)
    game.wait(0.5)  # 0.5s interval = 2 FPS cadence (matches VQA dynamic mode)
```

Feed the captured frames to VQA:
```bash
python visual_qa.py --log .vqa.log reference.png screenshots/frame_*.png
```

## Tips

- Screenshots go in `screenshots/` (gitignored)
- Use `game.wait()` between captures to let physics/animation advance
- For static scenes, one screenshot is enough
- For dynamic scenes, 4-8 frames at 0.5s intervals covers most verification needs
- All captures are engine-internal — no GPU detection, xvfb, or display setup needed
