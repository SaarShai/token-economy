from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


CONFIG_NAME = "token-economy.yaml"


@dataclass
class Config:
    repo_root: Path
    wiki_root: Path
    agent_adapter: str = "auto"
    context_max_tokens: int | str = "auto"
    refresh_threshold: float = 0.20
    default_scope: str = "project"
    model_registry: Path | None = None
    external_adapters: list[str] | None = None


def find_repo_root(start: str | Path | None = None) -> Path:
    cur = Path(start or Path.cwd()).resolve()
    if cur.is_file():
        cur = cur.parent
    for candidate in (cur, *cur.parents):
        if (candidate / CONFIG_NAME).exists() or (candidate / ".git").exists():
            return candidate
    return cur


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if value in {"[]", "[ ]"}:
        return []
    if value.startswith("[") and value.endswith("]"):
        body = value[1:-1].strip()
        if not body:
            return []
        return [parse_scalar(part.strip()) for part in body.split(",")]
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if value.lower() in {"auto", "none", "null"}:
        return "auto" if value.lower() == "auto" else None
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value.strip("\"'")


def load_simple_yaml(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_key: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line:
            continue
        if line.startswith((" ", "\t")) and current_key:
            item = line.strip()
            if item.startswith("- "):
                data.setdefault(current_key, [])
                if isinstance(data[current_key], list):
                    data[current_key].append(parse_scalar(item[2:]))
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            current_key = key.strip()
            value = value.strip()
            data[current_key] = [] if value == "" else parse_scalar(value)
    return data


def load_config(repo_root: str | Path | None = None) -> Config:
    root = find_repo_root(repo_root)
    path = root / CONFIG_NAME
    raw = load_simple_yaml(path) if path.exists() else {}
    wiki_root_raw = raw.get("wiki_root", ".")
    wiki_root = Path(str(wiki_root_raw)).expanduser()
    if not wiki_root.is_absolute():
        wiki_root = root / wiki_root
    model_registry_raw = raw.get("model_registry", "./models.yaml")
    model_registry = Path(str(model_registry_raw)).expanduser()
    if not model_registry.is_absolute():
        model_registry = root / model_registry
    return Config(
        repo_root=root,
        wiki_root=wiki_root.resolve(),
        agent_adapter=str(raw.get("agent_adapter", "auto")),
        context_max_tokens=raw.get("context_max_tokens", "auto"),
        refresh_threshold=float(raw.get("refresh_threshold", 0.20)),
        default_scope=str(raw.get("default_scope", "project")),
        model_registry=model_registry,
        external_adapters=raw.get("external_adapters", []) or [],
    )


def detect_agent() -> str:
    env = {k.lower() for k in __import__("os").environ}

    def host_key_contains(needle: str) -> bool:
        return any(needle in k and "api" not in k and "key" not in k and "token" not in k for k in env)

    if host_key_contains("codex"):
        return "codex"
    if host_key_contains("cursor"):
        return "cursor"
    if host_key_contains("gemini"):
        return "gemini"
    if host_key_contains("claude"):
        return "claude"
    return "codex"
