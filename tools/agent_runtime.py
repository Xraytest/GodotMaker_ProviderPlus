"""Agent runtime helpers for project-local GodotMaker tools."""
from __future__ import annotations

from pathlib import Path


AGENT_CLAUDE_CODE = "claude-code"
AGENT_CODEX = "codex"


def _read_yaml_scalar(path: Path, key: str) -> str | None:
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        current_key, value = stripped.split(":", 1)
        if current_key.strip() == key:
            value = value.strip().strip('"').strip("'")
            return value or None
    return None


def normalize_agent(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower().replace("_", "-")
    if normalized in {"codex", "openai-codex"}:
        return AGENT_CODEX
    if normalized in {"claude", "claude-code", "anthropic-claude-code"}:
        return AGENT_CLAUDE_CODE
    return None


def detect_agent(project_dir: Path) -> str:
    """Detect the selected coding agent for a published project."""
    config = project_dir / ".godotmaker" / "config.yaml"
    for key in ("agent", "agent_runtime"):
        agent = normalize_agent(_read_yaml_scalar(config, key))
        if agent:
            return agent

    # Backward-compatible fallback for older projects without `agent`.
    if (project_dir / ".agents").exists():
        return AGENT_CODEX
    return AGENT_CLAUDE_CODE


def agent_config_root(project_dir: Path, agent: str | None = None) -> Path:
    selected = normalize_agent(agent) or detect_agent(project_dir)
    if selected == AGENT_CODEX:
        return project_dir / ".agents"
    return project_dir / ".claude"


def agent_skill_root(project_dir: Path, agent: str | None = None) -> Path:
    return agent_config_root(project_dir, agent) / "skills"


def agent_runtime_mapping(project_dir: Path, agent: str | None = None) -> Path:
    selected = normalize_agent(agent) or detect_agent(project_dir)
    if selected == AGENT_CODEX:
        return project_dir / ".agents" / "references" / "runtime-mapping.md"
    return project_dir / ".claude" / "references" / "runtime-mapping.md"


def godotmaker_yaml(project_dir: Path, agent: str | None = None) -> Path:
    return agent_config_root(project_dir, agent) / "godotmaker.yaml"


def read_godot_path(project_dir: Path, default: str | None = None) -> str | None:
    value = _read_yaml_scalar(godotmaker_yaml(project_dir), "godot_path")
    return value if value else default
