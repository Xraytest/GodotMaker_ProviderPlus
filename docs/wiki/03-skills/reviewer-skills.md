# Reviewer Skills Reference

Reviewer skills are **post-implementation** code reviewers, not pre-implementation guides. They exist because LLMs consistently make the same Godot-specific mistakes -- physics callback safety, UI mouse filter defaults, TileMap API changes between Godot versions, and so on. Each reviewer skill encodes a curated list of these known gotchas and a checklist to catch them.

## Purpose

After a worker subagent writes code, the orchestrator dispatches a reviewer subagent. The reviewer:

1. Reads the implemented files.
2. Scans all 8 reviewer skill descriptions to determine which domains the code touches.
3. Runs the matching reviewers' checklists against the code.
4. Reports issues found, with references to specific gotchas.

The reviewer agent is **read-only** -- it must not modify project files. It only reports problems for the orchestrator or worker to fix.

## Consistent Structure

Every reviewer skill follows the same three-file pattern:

```
skills/reviewer/{domain}/
    SKILL.md        # Trigger conditions, review procedure, when-to-trigger list
    gotchas.md      # Known engine pitfalls with symptom/root-cause/correct-approach format
    checklist.md    # Static and runtime checks that map back to gotchas (S1 -> G1, etc.)
```

### gotchas.md format

Each gotcha follows a consistent structure:

```markdown
## G1. Short title [GDScript] [C#]

**Symptom**: What the developer sees when this goes wrong.

**Root cause**: Why the engine behaves this way.

**Correct approach**: The right way to handle it.

**Wrong approach**: Common mistakes (what the LLM typically generates).
```

### checklist.md format

Each check maps to a gotcha and provides a concrete procedure:

```markdown
### S1. Check name -> G1
Grep for [pattern]:
- [condition to flag]
- [expected pattern instead]
```

## Reviewer Skills Table

| Reviewer | Godot Subsystem | Key Triggers | Example Gotchas |
|---|---|---|---|
| physics | CollisionObject2D, RigidBody2D, CharacterBody2D, Area2D, collision layers, physics callbacks | `body_entered`, `collision_layer`, `_physics_process` with velocity | Physics callbacks cannot modify physics state; frame-rate dependent drag; collision layer bitmask vs layer-value API |
| animation | AnimationPlayer, AnimationTree, AnimatedSprite2D, SpriteFrames, state machines | `play()`, `travel()`, `active`, `callback_mode_process` | AnimationTree active flag, state machine travel vs start, SpriteFrames runtime manipulation |
| ui | Control, Container hierarchy, Button, Label, Theme, StyleBox, focus/mouse | `focus_mode`, `mouse_filter`, `grab_focus`, `gui_input` | Mouse filter defaults blocking input, container sizing, focus chain gaps |
| tilemap | TileMapLayer, TileSet, TileSetAtlasSource, terrain painting | `set_cell`, `erase_cell`, `get_cell_tile_data` | Godot 4.3 TileMap -> TileMapLayer migration, collision polygon setup on tiles |
| navigation | NavigationAgent2D/3D, NavigationRegion2D/3D, NavigationLink, NavigationObstacle | `target_position`, `velocity_computed`, `is_navigation_finished` | Navigation mesh bake timing, avoidance setup, safe_velocity usage |
| shader | ShaderMaterial, .gdshader, VisualShader, uniforms | `set_shader_parameter`, `hint_screen_texture`, instance uniforms | Shared vs unique ShaderMaterial, screen texture setup, uniform name mismatches |
| audio | AudioStreamPlayer, AudioStreamPlayer2D/3D, AudioServer, AudioBus | `preload()` of .ogg/.mp3, bus effects, `.finished` signal | Audio bus index vs name, stream resource sharing, polyphony limits |
| particles | GPUParticles2D/3D, CPUParticles2D/3D, ParticleProcessMaterial, trails | `trail_enabled`, sub-emitters, `amount`, emission control | GPU vs CPU particle differences, trail configuration, one-shot emission timing |

## How Reviewers Are Triggered

The orchestrator dispatches reviewers through the `reviewer-dispatch.md` protocol:

1. A worker subagent completes a task.
2. The orchestrator creates a **reviewer brief** specifying: what was implemented, which files to review, context about the systems involved.
3. A reviewer subagent (Sonnet model by default) receives the brief.
4. The reviewer reads each available domain skill's description and matches it against the code under review.
5. For each matched domain, the reviewer runs through the checklist items, grepping the code for known anti-patterns.
6. The reviewer produces a report listing issues found, each referencing a specific gotcha ID (e.g., "physics G1: direct queue_free in body_entered callback").

### Domain matching example

If a worker implemented a player movement system with CharacterBody2D and collision detection:

- **physics** matches: CharacterBody2D, collision layers, body_entered signal
- **animation** matches: if AnimatedSprite2D is used for player sprites
- **ui** does not match: no Control nodes involved
- The reviewer runs physics checklist items S1-S5+ and animation checklist items against the code

## Key Design Decision

Reviewers are deliberately separate from workers. Workers focus on getting code correct against the GDD and ECS architecture. Reviewers catch Godot-engine-specific traps that are orthogonal to business logic correctness. This separation means:

- Workers do not need to internalize every engine gotcha.
- Reviewers can be updated independently as new gotchas are discovered.
- The gotcha database grows over time without inflating worker prompts.
