# Project Configuration

Project-specific settings that control GodotMaker's behavior for a particular game project.

## Location

```
<project>/.godotmaker/config.yaml
```

Created by the publish system from `config/config.yaml.default`. Once created, it is never overwritten by subsequent publishes.

## Fields

| Field | Default | Description |
|---|---|---|
| `vqa_model` | `gemini-3-flash` | Gemini model used for visual quality assurance (VQA) checks. Any valid Gemini model name. |
| `worker_model` | `opus` | Model used for worker subagents (complex implementation tasks). |
| `verifier_model` | `sonnet` | Model used for verifier subagents (validation and checking). |
| `reviewer_model` | `sonnet` | Model used for reviewer subagents (code review and feedback). |
| `analyst_model` | `sonnet` | Model used for analyst subagents (metrics and analysis). |

## Default File

```yaml
# GodotMaker project configuration
# Edit these values to customize behavior
# Deployed to .godotmaker/config.yaml by publish script

# VQA model for visual quality checks (any Gemini model name)
# Default: gemini-3-flash
# Examples: gemini-3-flash, gemini-2.5-flash, gemini-2.0-flash
vqa_model: gemini-3-flash

# Agent model configuration
# Workers use opus for complex implementation tasks
# Verifiers, reviewers, and analysts use sonnet for lighter validation work
worker_model: opus
verifier_model: sonnet
reviewer_model: sonnet
analyst_model: sonnet
```

## When to Customize

- **VQA model**: Change if you want to use a different Gemini model for screenshot analysis. Newer or larger models may produce better results but cost more.
- **Worker model**: Workers perform the bulk of code generation. Opus is recommended for its stronger reasoning and code generation capabilities.
- **Verifier/reviewer/analyst models**: These perform lighter validation tasks. Sonnet provides a good cost/quality tradeoff. Switch to opus if you need higher accuracy for reviews.
