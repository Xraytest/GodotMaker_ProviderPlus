# Frequently Asked Questions

## General

### What Godot versions are supported?

Godot 4.4 and above. The `config/addon_versions.json` file maps Godot versions (4.3, 4.4, 4.5) to compatible addon versions. While 4.3 mappings exist, the recommended minimum is 4.4.

### Can I use C# instead of GDScript?

Yes. The project supports both GDScript and C#. The `addon_versions.json` file tracks addon compatibility for the .NET-enabled Godot builds. ECS components and systems can be written in either language.

### Where are metrics stored?

Metrics are written to two files inside the target project:

- `.godotmaker/metrics_current.jsonl` -- Events for the current session
- `.godotmaker/metrics.jsonl` -- Accumulated events across sessions

These are JSONL (one JSON object per line) files. They are gitignored by default.

## Skills and Reviewers

### How do I add a new reviewer skill?

Create a new directory under `skills/reviewer/` with three files:

```
skills/reviewer/your-domain/
  SKILL.md        Main skill prompt (role, scope, review instructions)
  checklist.md    Verification checklist for the domain
  gotchas.md      Common pitfalls and Godot-specific issues
```

See any existing reviewer (e.g., `skills/reviewer/physics/`) as a reference. Reviewer skills are post-implementation reviewers -- they check code after a worker has written it, not before.

### How do I write a new core skill?

Create a directory under `skills/core/` with at minimum a `SKILL.md` file. The orchestrator references skills by directory name. After creating the skill, publish it to a test project to verify it deploys correctly.

## Publishing and Deployment

### Why does publish.py initialize a git repository?

The orchestrator uses git worktrees to isolate parallel worker subagents. Worktree creation requires at least one commit in the repository. Without it, git fails with:

```
fatal: not a valid object name: HEAD
```

The publish script runs `git init` and `git commit --allow-empty` to satisfy this requirement.

### What does --force do on publish?

Two things:

1. Deletes the existing `.claude/skills/` directory before publishing, ensuring no stale files remain from a previous version
2. Skips interactive confirmation prompts for MINOR/MAJOR upgrades and allows downgrades

### How do I publish to multiple projects?

Run `publish.py` once per target:

```bash
python tools/publish.py /path/to/project-a
python tools/publish.py /path/to/project-b
```

Each target gets its own independent copy of all GodotMaker files.

## Hooks and Enforcement

### How do I skip hook enforcement?

Three options:

1. **Use --force on publish** -- Overwrites `settings.json`, which you can then edit
2. **Edit settings.json** -- In the target project's `.claude/settings.json`, remove or comment out hook entries for the events you want to skip
3. **Let anti-deadloop kick in** -- After 5 consecutive blocks from the same hook, the system automatically allows the action to proceed (prevents infinite loops)

### What if a hook keeps blocking my work?

The anti-deadloop mechanism prevents infinite blocking. After 5 consecutive blocks from `check_completion` or `check_worker_report`, the hook automatically allows the action. The block counter resets when a different hook blocks or when the action succeeds.

If you need to debug a hook, run it manually with test input:

```bash
echo '{"event": "Stop", "session": {}}' | python .godotmaker/hooks/check_completion.py
```

### Which hooks fire on which events?

The hook registration is defined in `config/settings.json`:

| Event | Hooks |
|---|---|
| SessionStart | `session_start.py` |
| PreToolUse (Write/Edit) | `check_file_permissions.py`, `stage_reminder.py` |
| PreToolUse (Agent) | `check_stage_prerequisites.py` |
| PreToolUse (Read) | `check_asset_access.py` |
| SubagentStart | `log_subagent.py` |
| SubagentStop | `log_subagent.py`, `check_worker_report.py` |
| Stop | `check_completion.py` |

## Reports

### How do I generate an HTML report?

Use the shell scripts:

```bash
# Unix/macOS
bash shell/report.sh .godotmaker/metrics.jsonl

# Windows
shell\report.bat .godotmaker\metrics.jsonl
```

These invoke the metrics reporter to generate an HTML report from the specified JSONL event log.

You can also run the reporter directly:

```bash
python -m hooks.metrics.reporter .godotmaker/metrics_current.jsonl -o report.html
```
