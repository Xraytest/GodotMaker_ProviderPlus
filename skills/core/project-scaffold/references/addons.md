# Addon Installation

Every GodotMaker project requires these dependencies.
Install them after scaffold, before running headless-build or tests.

## Version Compatibility — MANDATORY

Read `.claude/config/addon_versions.json` to determine the correct version for each addon.
The JSON maps Godot versions to compatible addon versions. You MUST use the exact tag specified.

**Steps:**
1. Detect Godot version: `godot --version` (e.g., "4.4.stable")
2. Extract major.minor (e.g., "4.4")
3. Look up the matching entry in `addon_versions.json` → `godot_versions["4.4"]`
4. For each addon, download the exact `tag` from the `repo`

If the Godot version is not in the mapping, use the closest lower version. If no match exists, report to the user — do NOT guess versions.

## Download Method

For each addon in the version mapping:

```bash
# Clone specific tag, copy addon directory, clean up
git clone --depth 1 --branch {tag} https://github.com/{repo}.git /tmp/{addon_name}
cp -r /tmp/{addon_name}/{install_path}/ {install_path}/
rm -rf /tmp/{addon_name}
```

## Post-Download Configuration

### gecs (ECS Framework)

If `"plugin": true` in the mapping:
- Add to `[editor_plugins]` in project.godot:
  ```
  [editor_plugins]
  enabled=PackedStringArray("res://addons/gecs/plugin.cfg")
  ```

### gdUnit4 (Test Framework)

If `"plugin": true` in the mapping:
- Add to `[editor_plugins]` in project.godot:
  ```
  enabled=PackedStringArray("res://addons/gecs/plugin.cfg", "res://addons/gdunit4/plugin.cfg")
  ```

### godot-e2e (E2E Testing)

If `"plugin": true` in the mapping:
- Add to `[editor_plugins]` in project.godot alongside gecs and gdUnit4:
  ```
  enabled=PackedStringArray("res://addons/gecs/plugin.cfg", "res://addons/gdunit4/plugin.cfg", "res://addons/godot_e2e/plugin.cfg")
  ```

The plugin automatically registers the `AutomationServer` autoload.

## godot-mcp (Runtime Debug Server)

Not a Godot addon — an npm package registered with Claude Code.

```bash
claude mcp add godot -e GODOT_PATH="<path_to_godot_executable>" -- npx @coding-solo/godot-mcp
```

This is handled by publish.sh/ps1 during project setup.

## Verification

After all addons are installed:

```bash
godot --headless --quit 2>&1
```

No `SCRIPT ERROR:` lines means success. Common errors:
- `World` class not found → gecs not installed or not enabled
- `GdUnitRunner` error → gdUnit4 version mismatch with Godot version
- `AutomationServer` error → godot-e2e plugin not enabled or addon files missing
