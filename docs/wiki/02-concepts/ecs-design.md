# Your Game's Architecture

GodotMaker generates games using ECS — Entity Component System — via the [gecs](https://github.com/csprance/gecs) addon. You don't need to understand ECS internals to use GodotMaker, but knowing the basics helps you read generated code and write better prompts.

## Why ECS?

When GodotMaker generates your game, it works inside a constraint: AI-written code must be readable, testable, and safe to extend. ECS gives three concrete benefits:

**Predictable.** A system does exactly what its name says — `MovementSystem` moves things, `DamageSystem` applies damage. There are no hidden state machines or inherited behaviors to trace. You can read any system in isolation and understand what it does.

**Testable.** Pure logic (movement math, AI decisions, damage calculations) can be tested without launching Godot. Tests set up a registry, add some components, call a system, and check the result. This runs in milliseconds and catches bugs before the game ever opens.

**Composable.** Entities get behavior by carrying components, not by extending classes. To make an enemy that also picks up items, you add a `PickupTag` component — you don't refactor an inheritance chain. This is far less error-prone for generated code.

## Components and Systems

**Components** are plain data containers. They store state, not logic.

```gdscript
# A component — just data
class_name TransformComp
var position: Vector2
var rotation: float
```

**Systems** are functions that process all entities carrying a specific set of components.

```gdscript
# A system — just logic
func process(registry: Registry, delta: float) -> void:
    for entity in registry.view([TransformComp, VelocityComp]):
        var t = registry.get_component(entity, TransformComp)
        var v = registry.get_component(entity, VelocityComp)
        t.position += v.direction * v.speed * delta
```

An entity is just an ID. Its behavior is entirely determined by which components it carries. A `[Transform, Sprite, Physics]` entity renders and collides. Remove `Physics` and it becomes a purely visual object — no subclassing needed.

## Scenes as Spawners

In your Godot scenes, you place **marker nodes** — lightweight placeholders that describe what should exist at runtime. They are not real game entities.

When the game starts, a converter reads the markers and creates ECS entities:

```
PlayerSpawnMarker   -> [TransformComp, PlayerTag, InputComp]
EnemySpawnerMarker  -> [TransformComp, SpawnerComp, EnemyTag]
TriggerZoneMarker   -> [TransformComp, AreaComp, TriggerEvent]
PickupMarker        -> [TransformComp, PickupItemComp]
```

This keeps the scene editor clean and your game simulation entirely inside ECS. The scene tree at runtime is reserved for UI and menus.

## Testing and TDD

Your game comes with tests automatically. Every mechanic GodotMaker generates is verified by a test before you ever play it — if movement, damage, or AI logic doesn't behave as specified, the test fails and the code is fixed before it reaches your project.

This means you don't have to discover bugs by playing. The test suite is the first player, and it checks each mechanic against the design intent you described in your prompt.

When you ask GodotMaker to add a new mechanic, it extends this test suite rather than patching untested code. Your game's test coverage grows with its feature set.
