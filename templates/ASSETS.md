# Assets: {Project Name}

## Art Direction

<!-- Visual style guide for asset generation. Established from reference.png. -->

- **Style:** {e.g., pixel art 16x16, hand-painted, low-poly, cel-shaded}
- **Color palette:** {dominant colors, mood}
- **Perspective:** {top-down, side-scroll, isometric, 3D third-person}
- **Lighting:** {flat, directional, ambient, dramatic}
- **Reference:** reference.png

## Asset Table

<!-- Master manifest of all visual assets. Updated as assets are generated. -->

| # | Name | Type | Size | Generation Params | File Path | Status |
|---|------|------|------|-------------------|-----------|--------|
| 1 | player_idle | sprite | 32x32 | {prompt or tool params} | assets/sprites/player_idle.png | pending |
| 2 | player_walk | spritesheet | 128x32 (4 frames) | {prompt or tool params} | assets/sprites/player_walk.png | pending |
| 3 | enemy_basic | sprite | 32x32 | {prompt or tool params} | assets/sprites/enemy_basic.png | pending |
| 4 | background_sky | background | 1280x720 | {prompt or tool params} | assets/backgrounds/sky.png | pending |
| ... | ... | ... | ... | ... | ... | ... |

## Animated Sprites

<!-- Spritesheet breakdown for animated assets. -->

### player_walk
- **File:** assets/sprites/player_walk.png
- **Frame size:** 32x32
- **Frames:** 4
- **FPS:** 8
- **Loop:** true
- **Directions:** {down, left, right, up} or {single}

### {animation_name}
- **File:** ...
- **Frame size:** ...
- **Frames:** ...
- **FPS:** ...
- **Loop:** ...
- **Directions:** ...

## 3D Models

<!-- Only for 3D projects. Omit section for 2D. -->

| # | Name | Format | Poly Budget | Generation Tool | File Path | Status |
|---|------|--------|-------------|-----------------|-----------|--------|
| 1 | player_model | .glb | ~2000 tris | {tripo3d / manual} | assets/models/player.glb | pending |
| ... | ... | ... | ... | ... | ... | ... |

## Audio

<!-- Sound effects and music. -->

| # | Name | Type | Duration | File Path | Status |
|---|------|------|----------|-----------|--------|
| 1 | jump_sfx | sfx | 0.3s | assets/audio/jump.wav | pending |
| 2 | bgm_main | music | loop | assets/audio/bgm_main.ogg | pending |
| ... | ... | ... | ... | ... | ... |

## Budget Tracking

<!-- Track generation costs if using paid APIs. -->

| Asset | Tool | Cost | Notes |
|-------|------|------|-------|
| player_idle | {image gen API} | $0.00 | |
| player_model | tripo3d | $0.00 | |
| **Total** | | **$0.00** | |

## Post-Processing Notes

<!-- Any manual steps needed after generation. -->

- {asset}: needs background removal (rembg)
- {spritesheet}: needs grid slicing (grid_slice.py)
- {model}: needs scale adjustment to match game units
