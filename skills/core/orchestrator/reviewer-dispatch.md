# Reviewer Dispatch Protocol

Dispatch a reviewer for every completed worker task. The reviewer decides which domain-specific reviewer skills to run.

**Agent definition:** `.claude/agents/reviewer.md` — system prompt loaded automatically via `subagent_type: "reviewer"`.

## Agent Call

```
Agent({
  subagent_type: "reviewer",
  description: "Reviewer: review {task_name}",
  model: "{reviewer_model from .godotmaker/config.yaml, default: sonnet}",
  prompt: "{reviewer brief below}"
})
```

## Reviewer Brief Template

```
## Review: {what was implemented}                       [REQUIRED]

### Project Path                                         [REQUIRED]
{Absolute path to the Godot project}

### Files to Review                                      [REQUIRED]
- {file path}: {what it contains}

### Context                                              [REQUIRED]
{What the system does, which Components/Systems are involved}

### Specific Concerns                                    [OPTIONAL]
{Anything you want the reviewer to pay special attention to}
```
