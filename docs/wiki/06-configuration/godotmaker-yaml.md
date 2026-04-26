# godotmaker.yaml

Host-specific configuration file that stores local tool paths. This file is per-machine and should not be committed to version control.

## Location

```
<project>/.claude/godotmaker.yaml
```

This path is gitignored (the publish system adds `.claude/` to `.gitignore`).

## Purpose

Different developers (or the same developer on different machines) may have Godot installed at different paths. `godotmaker.yaml` stores these host-specific paths so that skills and hooks can locate tools without hardcoding paths or relying on PATH.

## Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `godot_path` | string | `"godot"` | Full path to the Godot executable, or just `"godot"` if it is on PATH |

## Example

```yaml
# Host-specific tool paths -- not committed to git
godot_path: "C:/Godot/Godot_v4.4-stable_win64.exe"
```

## How It Is Created

On the first publish to a project, `tools/publish.py` checks if `.claude/godotmaker.yaml` exists. If not, it runs an interactive prompt:

```
No godotmaker.yaml found. Let's create one.
Enter the full path to your Godot executable
  (e.g. C:/path/to/Godot_v4.4-stable_win64.exe)
godot_path: _
```

If the user presses Enter without providing a path, the value defaults to `"godot"` (assumes Godot is on PATH).

On subsequent publishes, the file is never overwritten.

## How Skills Read It

Skills use the `_read_config.sh` helper script (published alongside skills at `.claude/skills/_read_config.sh`):

```bash
GODOT=$(bash "${CLAUDE_SKILL_DIR}/../_read_config.sh" godot_path)
```

The helper:

1. Locates `.claude/godotmaker.yaml` relative to its own path.
2. Parses the YAML (simple key-value extraction; handles both quoted and unquoted values).
3. Returns the value for the requested key.
4. Falls back to a built-in default if the file is missing or the key is not found.

### Built-in defaults

| Key | Default |
|---|---|
| `godot_path` | `"godot"` |

If a key has no built-in default and is not found in the file, the helper exits with an error.
