from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .tokens import estimate_tokens, trim_to_tokens


PATH_RE = re.compile(r"(?P<path>(?:/|\.{1,2}/|[\w.-]+/)[\w./ @+-]+\.[A-Za-z0-9_+-]+)")
CMD_RE = re.compile(r"(?:cmd|command|bash|shell)[\"': ]+([^\\n]{3,240})", re.IGNORECASE)
ERR_RE = re.compile(r"((?:error|exception|traceback|failed|fatal)[^\n]{0,240})", re.IGNORECASE)


def resolve_max_tokens(value: int | str | None) -> int:
    if isinstance(value, int):
        return value
    env = os.environ.get("TOKEN_ECONOMY_CONTEXT_MAX")
    if env and env.isdigit():
        return int(env)
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return 128_000


def status_for_text(text: str, max_tokens: int | str | None = None, threshold: float = 0.20) -> dict[str, Any]:
    used = estimate_tokens(text)
    maximum = resolve_max_tokens(max_tokens)
    ratio = used / maximum if maximum else 0.0
    return {
        "estimated_tokens": used,
        "max_tokens": maximum,
        "ratio": round(ratio, 4),
        "threshold": threshold,
        "action": "checkpoint" if ratio >= threshold else "continue",
    }


def status_for_files(paths: list[Path], max_tokens: int | str | None = None, threshold: float = 0.20) -> dict[str, Any]:
    chunks = []
    for path in paths:
        if path.exists() and path.is_file():
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    return status_for_text("\n".join(chunks), max_tokens=max_tokens, threshold=threshold)


def extract_transcript_facts(text: str) -> dict[str, list[str]]:
    paths = sorted(set(m.group("path").strip() for m in PATH_RE.finditer(text)))[:80]
    commands = sorted(set(m.group(1).strip().strip("\"'") for m in CMD_RE.finditer(text)))[:50]
    errors = sorted(set(m.group(1).strip() for m in ERR_RE.finditer(text)))[:50]
    return {"files": paths, "commands": commands, "errors": errors}


def checkpoint(
    repo_root: Path,
    goal: str = "",
    plan: str = "",
    transcript: Path | None = None,
    max_packet_tokens: int = 2000,
) -> dict[str, Any]:
    state_dir = repo_root / ".token-economy" / "checkpoints"
    state_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    transcript_text = ""
    if transcript and transcript.exists():
        transcript_text = transcript.read_text(encoding="utf-8", errors="replace")
    facts = extract_transcript_facts(transcript_text)
    l1 = repo_root / "L1_index.md"
    l1_pointer = f"- L1 index: `{l1}`" if l1.exists() else "- L1 index: missing; run `./te wiki index`."
    packet = f"""# Fresh Session Packet

Instruction: Start in plan mode. Think step by step. Create a robust plan before executing.

## Goal
{goal or "Continue the current Token Economy task."}

## Current Plan
{plan or "Inspect repo state, retrieve relevant wiki/context on demand, then execute verified steps."}

## Memory Pointers
{l1_pointer}
- Wiki search: `./te wiki search "<query>"`
- Recent context: `./te context status`
- L2 facts: `L2_facts/`
- L3 SOPs: `L3_sops/`
- L4 archive: `L4_archive/`

## Touched Files
{format_list(facts["files"])}

## Commands Seen
{format_list(facts["commands"])}

## Errors Seen
{format_list(facts["errors"])}

## Open Decisions
- Retrieve relevant pages before deciding.
- Keep Caveman Ultra unless user asks for detail.
- Document durable facts only after verified execution.
"""
    packet = trim_to_tokens(packet, max_packet_tokens)
    path = state_dir / f"{ts}-fresh-session.md"
    path.write_text(packet, encoding="utf-8")
    return {"path": str(path), "tokens": estimate_tokens(packet), "packet": packet}


def format_list(items: list[str]) -> str:
    if not items:
        return "- none captured"
    return "\n".join(f"- `{item}`" for item in items[:40])

