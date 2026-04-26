# Game Plan: {Name}

<!-- Decomposed from GDD.md during Stage 1b. See GDD.md for full game design. -->

## Game Description

{Summary from GDD §1 (Game Overview) and §2 (Core Gameplay Loop).}

## Risk Tasks

<!-- Omit this section entirely if no risks identified. -->
<!-- Risk taxonomy for ECS: procedural generation, procedural animation,
     sprite/character animations, complex physics, custom shaders,
     runtime geometry, dynamic navigation, complex camera systems.
     These fail unpredictably and need isolation before main build. -->

### 1. {Risk Feature}
- **Why isolated:** {what makes this algorithmically hard}
- **Approach:** {algorithmic strategy or key constraints}
- **Systems:** {which systems this task implements — e.g., ProceduralTerrainSystem}
- **Components:** {which components this task defines — e.g., TerrainChunk, HeightMap}
- **Verify:**
  - {specific criteria targeting the failure mode}
  - DAG check passes with new systems integrated
  - gdUnit tests cover the core algorithm

### 2. {Risk Feature}
- **Why isolated:** ...
- **Approach:** ...
- **Systems:** ...
- **Components:** ...
- **Verify:** ...

## Main Build

{What to build — all routine systems. High-level, not implementation recipes.}

### Systems & Components

<!-- List the systems and components implemented in this phase. -->

| System | Components (reads) | Components (writes) | Purpose |
|--------|--------------------|---------------------|---------|
| MovementSystem | Transform, MovementIntent | Transform | Apply movement to entities |
| RenderSystem | Transform, SpriteComp | — | Project sprite nodes into scene tree |
| ... | ... | ... | ... |

### Assets Needed

<!-- Visual assets the game needs — type, approximate size, visual role. Omit if none. -->

- {asset description}
- **Terrain approach:** Sprite placement (individual scene elements) | N/A

### Verify

- Player input -> entity response feels correct
- Movement direction matches input
- Animation direction matches movement direction
- Physics entities respond to gravity/collision
- UI readable, no overflow or overlap
- No missing textures (magenta/checkerboard)
- {Game-specific checks}
- Gameplay flow matches game description
- No visual glitches, clipping, or placeholder assets
- reference.png consistency: color palette, scale, camera angle, visual density
- DAG check passes (no circular node-creation dependencies)
- All gdUnit tests pass (pure logic systems + materialization systems)
- Optional VQA validation on screenshots
- **Presentation video:** ~30s cinematic MP4 showcasing gameplay
  - Write test/Presentation.gd (SceneTree script), ~900 frames at 30 FPS
  - Output: screenshots/presentation/gameplay.mp4

## Task Status

<!-- Update after each task completes. This is the resume point. -->

| # | Task | Status | Notes |
|---|------|--------|-------|
| R1 | {Risk task 1} | pending | |
| R2 | {Risk task 2} | pending | |
| M | Main build | pending | |
| V | Presentation video | pending | |
