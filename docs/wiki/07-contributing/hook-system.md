# Hook System Overview

GodotMaker uses Python hook scripts to enforce pipeline rules during Claude Code sessions. Hooks intercept events such as file writes, agent dispatches, and session stop attempts. They can block the action with an error message, allow it silently, or inject additional context into the conversation.

## How Hooks Work

Each hook is a Python script that receives event data as JSON on stdin. Based on the event, the hook either:

- **Blocks** the action by printing a JSON decision to stdout and exiting with code 0.
- **Allows** the action by exiting with code 0 silently (no stdout), or by printing an `additionalContext` payload.
- **Crashes gracefully** -- if a hook errors out, the pipeline continues. Metrics collection never breaks the build.

Hooks are registered in `config/settings.json` and deployed to `.godotmaker/hooks/` via the publish script.

## Event Types

GodotMaker registers hooks on six Claude Code event types:

| Event | Matcher | Hooks Fired | Purpose |
|-------|---------|-------------|---------|
| `SessionStart` | (none) | `session_start.py` | Initialize metrics, reset state, display version |
| `PreToolUse` | `Write\|Edit` | `check_file_permissions.py`, `stage_reminder.py` | Enforce write permissions, validate stage outputs |
| `PreToolUse` | `Agent` | `check_stage_prerequisites.py` | Block worker dispatch if prerequisites missing |
| `PreToolUse` | `Read` | `check_asset_access.py` | Block orchestrator from reading asset images |
| `SubagentStart` | (none) | `log_subagent.py` | Record subagent dispatch with role detection |
| `SubagentStop` | (none) | `log_subagent.py`, `check_worker_report.py` | Record outcome, validate report format |
| `Stop` | (none) | `check_completion.py` | Final gate: project completeness + diligence |

The `matcher` field filters which tool triggers the hook. For example, `Write|Edit` means the hook only fires when the Write or Edit tool is invoked, not for other PreToolUse events.

## Decision Protocol

### Blocking a PreToolUse action

The hook prints a JSON object to stdout with `permissionDecision: "deny"`:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Orchestrator cannot write game code directly (player.gd). Dispatch a Worker subagent to implement this."
  }
}
```

Claude Code reads this output, cancels the tool call, and shows the reason to the agent.

### Allowing with additional context

The hook prints a JSON object with `additionalContext` instead of a permission decision:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": "[Stage 3 complete] Next: Stage 4. Read the detail file before proceeding: stages/stage4_assets.md"
  }
}
```

The action proceeds, and the context string is injected into the conversation.

### Allowing silently

The hook exits with code 0 and prints nothing to stdout. The action proceeds without any additional context.

### Blocking a Stop action

The Stop event uses a different JSON format:

```json
{
  "decision": "block",
  "reason": "Cannot finish -- issues found:\n  Dispatched 3 workers but 0 verifiers."
}
```

### Blocking a SubagentStop action

Same format as Stop:

```json
{
  "decision": "block",
  "reason": "Worker report missing required sections: Tests, Build."
}
```

## Configuration

Hooks are mapped to events in `config/settings.json`. The structure maps event names to arrays of matcher+hooks pairs:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {"type": "command", "command": "python .godotmaker/hooks/session_start.py"}
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {"type": "command", "command": "python .godotmaker/hooks/check_file_permissions.py"},
          {"type": "command", "command": "python .godotmaker/hooks/stage_reminder.py"}
        ]
      }
    ]
  }
}
```

When multiple hooks are registered for the same event+matcher, they run in order. If any hook blocks, the action is denied -- subsequent hooks for that event are not guaranteed to run.

## Anti-Deadloop Protection

All blocking hooks implement a force-allow mechanism to prevent infinite retry loops. When a hook has blocked the same agent N times (typically `BLOCK_LIMIT = 5`), it stops blocking and allows the action with a warning:

```
POTENTIAL BUG: Force-allowing worker report after 5 blocks.
Agent w1 could not satisfy report validation.
Report this to the user -- unresolved quality issues may remain.
```

This applies to:

| Hook | State Key | Limit |
|------|-----------|-------|
| `check_worker_report.py` | `worker_report_block:{agent_id}` | 5 per agent |
| `check_completion.py` | `stop_block_count` | 5 per session |

Block counts are tracked in `.godotmaker/state.json` and reset at session start.

## Stage Awareness

Some hooks only enforce their rules at later pipeline stages:

- **`check_completion.py`** only runs its full checks (project completeness, diligence, E2E coverage) at stage >= 7 (integration). At earlier stages, the orchestrator can stop freely without triggering the completion gate. This allows the orchestrator to pause mid-pipeline for user input without being blocked.

- **`stage_reminder.py`** validates stage outputs against `config/stage_schemas.json` whenever the orchestrator writes to `.godotmaker/stage.json`. The validation runs programmatic checks that are stage-specific (e.g., stage 4 checks for reference images, stage 7 checks for verifier events).

## Input Format

All hooks receive a JSON object on stdin. The exact fields depend on the event type:

| Field | Present In | Description |
|-------|-----------|-------------|
| `hook_event_name` | All | Event type string (e.g., `"PreToolUse"`, `"SubagentStop"`) |
| `tool_name` | PreToolUse | Tool being invoked (e.g., `"Write"`, `"Agent"`, `"Read"`) |
| `tool_input` | PreToolUse | Tool parameters (e.g., `{"file_path": "...", "content": "..."}`) |
| `agent_id` | All | Empty string for orchestrator, non-empty for subagents |
| `agent_type` | SubagentStart/Stop | Agent type string |
| `description` | SubagentStart | Dispatch description (used for role detection) |
| `last_assistant_message` | SubagentStop | Full text of the subagent's final response |

## See Also

- [Hook Reference](hook-reference.md) -- detailed documentation for each hook script
- [Metrics and State](metrics-and-state.md) -- event logging, state management, and HTML reports
