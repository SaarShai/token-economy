from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from math import ceil
from pathlib import Path
from typing import Any


PATH_RE = re.compile(r"(?P<path>(?:/|\.{1,2}/|[\w.-]+/)[\w./ @+-]+\.[A-Za-z0-9_+-]+)")
CMD_RE = re.compile(r"(?:cmd|command|bash|shell)[\"': ]+([^\\n]{3,240})", re.IGNORECASE)
ERR_RE = re.compile(r"((?:error|exception|traceback|failed|fatal)[^\n]{0,240})", re.IGNORECASE)
RELAY_NAME_RE = re.compile(r"^Relay\[(?P<version>\d+)\]:\s*(?P<name>.+)$")


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, ceil(len(text) / 4) + text.count("\n"))


def relay_session_name(name: str | None = None, version: str = "01") -> str:
    session = name or "auto-context-refresh"
    if session.startswith("Relay["):
        return session
    return f"Relay[{version}]: {session}"


def next_relay_session_name(previous: str | None = None, fallback: str | None = None, version: str = "01") -> str:
    source = (previous or fallback or "auto-context-refresh").strip()
    match = RELAY_NAME_RE.match(source)
    if match:
        return f"Relay[{int(match.group('version')) + 1:02d}]: {match.group('name')}"
    if fallback and fallback != source:
        return relay_session_name(fallback, version)
    return relay_session_name(source, version)


def current_codex_transcript(thread_id: str | None = None, sessions_root: Path | None = None) -> Path | None:
    target = thread_id or os.environ.get("CODEX_THREAD_ID")
    if not target:
        return None
    root = sessions_root or (Path.home() / ".codex" / "sessions")
    if not root.exists():
        return None
    matches = sorted(root.rglob(f"*{target}*.jsonl"), key=lambda path: path.stat().st_mtime, reverse=True)
    return matches[0] if matches else None


def extract_transcript_facts(text: str) -> dict[str, list[str]]:
    paths = sorted(set(match.group("path").strip().rstrip(".,)") for match in PATH_RE.finditer(text)))[:200]
    commands = [match.group(1).strip() for match in CMD_RE.finditer(text)][:80]
    errors = [match.group(1).strip() for match in ERR_RE.finditer(text)][:80]
    decisions = []
    for line in text.splitlines():
        if re.search(r"\b(decision|decided|choose|chosen|because|reason)\b", line, re.IGNORECASE):
            decisions.append(line.strip()[:300])
        if len(decisions) >= 80:
            break
    return {"files": paths, "commands": commands, "errors": errors, "decisions": decisions}


def format_list(items: list[str], max_items: int = 8, max_chars: int = 140) -> str:
    if not items:
        return "- none captured"
    lines = []
    for item in items[:max_items]:
        value = item if len(item) <= max_chars else item[: max_chars - 15].rstrip() + " ...[trimmed]"
        lines.append(f"- `{value}`")
    if len(items) > max_items:
        lines.append(f"- `...[{len(items) - max_items} more omitted; ask old session or inspect transcript if needed]...`")
    return "\n".join(lines)


def parse_handoff_metadata(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    meta: dict[str, str] = {}
    for raw in parts[1].splitlines():
        if ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        meta[key.strip()] = value.strip().strip("\"'")
    return meta


def checkpoint(
    repo_root: Path,
    goal: str,
    plan: str = "",
    transcript: Path | None = None,
    max_packet_tokens: int = 2000,
) -> dict[str, Any]:
    state_dir = repo_root / ".relay-session" / "checkpoints"
    state_dir.mkdir(parents=True, exist_ok=True)
    transcript_text = transcript.read_text(encoding="utf-8", errors="replace") if transcript and transcript.exists() else ""
    facts = extract_transcript_facts(transcript_text)
    old_thread_id = os.environ.get("CODEX_THREAD_ID") or "none"
    old_transcript = str(transcript) if transcript else "none"
    start = repo_root / "start.md"
    start_pointer = f"- Start file: `{start}`" if start.exists() else "- Start file: none; use this handoff plus repo retrieval."
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    iso = datetime.now(timezone.utc).isoformat()
    task_slug = re.sub(r"[^a-zA-Z0-9]+", "-", (goal or "relay-session").lower()).strip("-") or "relay-session"
    packet = f"""---
type: handoff
from-session: local
created: {iso}
next-mode: plan-first
old-thread-id: {old_thread_id}
old-transcript: {old_transcript}
old-session-query-policy: explicit-only
---

# HANDOFF - {task_slug}

## 1. Current task
{goal or "Continue current work."}

## 2. What done
- Handoff generated as a lean continuation packet.

## 3. What in-progress
- {plan or "Inspect repo state, retrieve narrowly, then execute verified steps."}

## 4. What next
- Read this handoff and `start.md` if present only.
- Verify this is a fresh successor context.
- Build plan before execution.

## 5. Key files touched
{format_list(facts["files"])}

## 6. Key decisions
{format_list(facts["decisions"])}

## 7. Retrieval pointers
{start_pointer}
- Ask old only for a specific missing fact after repo retrieval is insufficient.

## 8. Open questions
- none captured

## 9. Instructions for next agent
- Start in plan mode. Think step-by-step. Create a compact plan before executing.
- Do not load broad archives until retrieval proves relevance.
- If a needed fact is absent and repo retrieval is insufficient, ask the old session explicitly:
  `python3 -m relay_session.cli ask-old --handoff <handoff-file> --question "<specific missing fact>"`
- Record old-session answers only if they change ongoing work or the next handoff.

## Commands Seen
{format_list(facts["commands"])}

## Errors Seen
{format_list(facts["errors"])}
"""
    if estimate_tokens(packet) > max_packet_tokens:
        packet = packet.replace(format_list(facts["commands"]), "- omitted to preserve relay instructions")
        packet = packet.replace(format_list(facts["errors"]), "- omitted to preserve relay instructions")
    path = state_dir / f"{ts}-fresh-session.md"
    path.write_text(packet, encoding="utf-8")
    return {"path": str(path), "tokens": estimate_tokens(packet), "packet": packet}


def lint_handoff(path: Path, max_tokens: int = 2000) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    required = [
        "old-session-query-policy: explicit-only",
        "old-thread-id:",
        "old-transcript:",
        "## 1. Current task",
        "## 9. Instructions for next agent",
        "Start in plan mode",
        "ask-old",
    ]
    missing = [item for item in required if item not in text]
    tokens = estimate_tokens(text)
    return {"path": str(path), "tokens": tokens, "max_tokens": max_tokens, "missing": missing, "ok": not missing and tokens <= max_tokens}


def ask_old_from_transcript(transcript: Path, question: str, max_snippets: int = 8) -> dict[str, Any]:
    if not transcript.exists():
        return {"ok": False, "mode": "transcript", "error": "old transcript unavailable", "transcript": str(transcript)}
    text = transcript.read_text(encoding="utf-8", errors="replace")
    terms = [term.lower() for term in re.findall(r"[A-Za-z0-9_.-]{4,}", question)][:12]
    lines = text.splitlines()
    scored: list[tuple[int, int]] = []
    for i, line in enumerate(lines):
        score = sum(1 for term in terms if term in line.lower())
        if score:
            scored.append((score, i))
    scored.sort(key=lambda row: (-row[0], row[1]))
    snippets = []
    for _, idx in scored[:max_snippets]:
        start = max(0, idx - 1)
        end = min(len(lines), idx + 2)
        snippets.append({"line": idx + 1, "text": "\n".join(line.strip() for line in lines[start:end] if line.strip())[:1200]})
    return {"ok": bool(snippets), "mode": "transcript", "question": question, "transcript": str(transcript), "snippets": snippets}


def ask_old_plan(repo_root: Path, handoff: Path, question: str, execute: bool = False) -> dict[str, Any]:
    meta = parse_handoff_metadata(handoff)
    old_thread_id = meta.get("old-thread-id")
    old_transcript = meta.get("old-transcript")
    if old_thread_id and old_thread_id != "none":
        return {
            "ok": True,
            "mode": "codex-old-thread",
            "execute": execute,
            "thread_id": old_thread_id,
            "handoff": str(handoff),
            "question": question,
            "prompt": "Answer only this specific relay follow-up from your old session context. Do not continue implementation. Question: " + question,
        }
    if old_transcript and old_transcript != "none":
        transcript = Path(old_transcript).expanduser()
        if not transcript.is_absolute():
            transcript = repo_root / transcript
        return ask_old_from_transcript(transcript, question)
    return {"ok": False, "mode": "unavailable", "handoff": str(handoff), "question": question, "error": "old session unavailable"}

