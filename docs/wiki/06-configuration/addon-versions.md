# Addon Versions

Pins the exact versions of Godot addons that GodotMaker depends on, mapped to specific Godot engine versions.

> This file is managed by GodotMaker automatically. You typically do not need to edit it manually.

## Location

```
config/addon_versions.json
```

This file is part of GodotMaker's configuration.

## Purpose

When GodotMaker sets up a new game project, it reads `addon_versions.json` to determine which addon versions to download. This ensures reproducibility -- every project generated with the same GodotMaker version gets the same tested addon versions.

## Tracked Addons

| Addon | Repository | Purpose |
|---|---|---|
| **gecs** | [csprance/gecs](https://github.com/csprance/gecs) | ECS framework for Godot |
| **gdunit4** | [MikeSchulze/gdUnit4](https://github.com/MikeSchulze/gdUnit4) | Unit testing framework |
| **godot_e2e** | [RandallLiuXin/godot-e2e](https://github.com/RandallLiuXin/godot-e2e) | End-to-end testing framework |

## Godot Version Compatibility Matrix

| Godot Version | gecs | gdunit4 | godot_e2e |
|---|---|---|---|
| **4.3** | v7.1.0 | v5.1.1 | v1.1.0 |
| **4.4** | v7.1.0 | v5.1.1 | v1.1.0 |
| **4.5** | v7.1.0 | v6.1.0 | v1.1.0 |

Key version notes:

- **gecs v7.1.0** is compatible across all listed Godot versions.
- **gdunit4 v5.x** is for Godot 4.3 and 4.4. **gdunit4 v6.x** requires Godot 4.5 or later.
- **godot_e2e v1.1.0** is compatible across all listed Godot versions. The plugin registers automatically on install.

## Updating

Addon versions are updated when you upgrade GodotMaker. After upgrading, re-run `publish.py` to update your project.
