from __future__ import annotations

"""Context fill meter for auto-handoff.

Estimates how full the active context is from the Claude Code transcript JSONL,
counting *message content* (text the model actually sees) rather than raw JSON
bytes, so the percentage isn't inflated by transcript scaffolding (event keys,
tool-call envelopes, uuids).

Self-contained: depends only on the sibling `tokens.py`. No import from the
`handoff` skill (the user's constraint is to keep these decoupled).
"""

import json
import os
from pathlib import Path
from typing import Any

from tokens import estimate_tokens

# Opus 4.x context window. Override with TOKEN_ECONOMY_CONTEXT_MAX for other models.
DEFAULT_MAX = 200_000


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    # Accept either 0.50 or 50 (percent) forms.
    return value / 100 if value > 1 else value


def resolve_max_tokens() -> int:
    env = os.environ.get("TOKEN_ECONOMY_CONTEXT_MAX")
    if env and env.strip().isdigit():
        return int(env)
    return DEFAULT_MAX


def _block_text(block: Any) -> str:
    """Pull human-readable text from one content block (best-effort)."""
    if isinstance(block, str):
        return block
    if not isinstance(block, dict):
        return ""
    if isinstance(block.get("text"), str):
        return block["text"]
    inner = block.get("content")
    if isinstance(inner, str):
        return inner
    if isinstance(inner, list):
        return "\n".join(_block_text(sub) for sub in inner)
    # tool_use input / other structured payloads still consume context — count them.
    if block.get("type") == "tool_use" and isinstance(block.get("input"), (dict, list)):
        return json.dumps(block["input"], separators=(",", ":"))
    return ""


def _event_text(obj: Any) -> str:
    """Extract the model-visible text from a single transcript event object."""
    if not isinstance(obj, dict):
        return ""
    content = None
    msg = obj.get("message")
    if isinstance(msg, dict):
        content = msg.get("content")
    if content is None:
        content = obj.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(_block_text(b) for b in content)
    return ""


def transcript_text(transcript: Path | None) -> str:
    """Concatenate model-visible text across all transcript events.

    Falls back to the raw line when an event can't be parsed, so a malformed
    line never makes us *undercount* fill (safer to over-trigger than to miss).
    """
    if not transcript or not transcript.exists():
        return ""
    parts: list[str] = []
    for line in transcript.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            text = _event_text(json.loads(line))
        except Exception:
            text = line
        parts.append(text if text else line)
    return "\n".join(parts)


def fill_status(transcript: Path | None, threshold: float | None = None) -> dict[str, Any]:
    """Return fill ratio + an action: continue | warn | refresh.

    threshold default 0.50, overridable via REFRESH_AT_PCT (0.50 or 50 forms).
    warn fires 0.15 below refresh (overridable via WARN_AT_PCT).
    """
    text = transcript_text(transcript)
    used = estimate_tokens(text)
    maximum = resolve_max_tokens()
    refresh = _env_float("REFRESH_AT_PCT", threshold if threshold is not None else 0.50)
    warn = _env_float("WARN_AT_PCT", max(0.0, refresh - 0.15))
    ratio = used / maximum if maximum else 0.0
    action = "refresh" if ratio >= refresh else "warn" if ratio >= warn else "continue"
    return {
        "estimated_tokens": used,
        "max_tokens": maximum,
        "ratio": round(ratio, 4),
        "pct": round(ratio * 100, 2),
        "warn_threshold": warn,
        "refresh_threshold": refresh,
        "threshold": refresh,
        "action": action,
    }
