from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from math import ceil
from pathlib import Path
from typing import Any


PATH_RE = re.compile(r"(?P<path>(?:/|\.{1,2}/|[\w.-]+/)[\w./ @+-]+\.[A-Za-z0-9_+-]+)")
PATCH_PATH_RE = re.compile(r"^\*\*\* (?:Update|Add|Delete) File: (?P<path>.+)$", re.MULTILINE)
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
    decisions: list[str] = []
    seen: set[str] = set()

    def add(line: str) -> None:
        cleaned = re.sub(r"\s+", " ", line.strip().lstrip("- ").strip("`"))
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            decisions.append(cleaned)

    decision_re = re.compile(r"\b(confirmed|conclusion|rule|fixed|not solved|caveat|current read|important|should|should not|worked|restarting codex)\b", re.IGNORECASE)
    for role, body in transcript_messages(text)[-24:]:
        if role not in {"user", "assistant"}:
            continue
        for raw in body.splitlines():
            line = raw.strip()
            if line.endswith(":") or len(line) < 8:
                continue
            if decision_re.search(line):
                add(line)
    return {"files": [], "commands": [], "errors": [], "decisions": decisions[:8]}


def _message_text(payload: dict[str, Any]) -> str:
    content = payload.get("content")
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts = []
    for item in content:
        if not isinstance(item, dict):
            continue
        value = item.get("text") or item.get("input_text")
        if isinstance(value, str):
            parts.append(value)
    return "\n".join(parts).strip()


def transcript_messages(text: str) -> list[tuple[str, str]]:
    messages: list[tuple[str, str]] = []
    for raw in text.splitlines():
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            continue
        payload = event.get("payload") if event.get("type") == "response_item" else {}
        if isinstance(payload, dict) and payload.get("type") == "message":
            role = payload.get("role")
            if role in {"user", "assistant"}:
                body = _message_text(payload)
                if body and not body.startswith("<turn_aborted>"):
                    messages.append((role, body))
    return messages


def _summary_lines(body: str) -> list[str]:
    lines: list[str] = []
    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(("-", "*")):
            line = line.lstrip("-* ").strip()
        if line.endswith(":"):
            continue
        if len(line) < 8:
            continue
        if re.search(r"\b(ok: true|passed|listed_name|thread_named|backend|sidebar|ui|commit|pushed|reverted|installed|fixed|launched|thread id)\b", line, re.IGNORECASE):
            lines.append(line)
    return lines


def compact_summary(text: str) -> list[str]:
    messages = transcript_messages(text)
    items: list[str] = []
    seen: set[str] = set()

    def add(item: str) -> None:
        clean = re.sub(r"\s+", " ", item).strip()
        if clean and clean not in seen:
            seen.add(clean)
            items.append(clean)

    for role, body in messages[-16:]:
        if role == "user":
            add("User asked: " + body.splitlines()[0].strip())
            continue
        for line in _summary_lines(body)[:5]:
            add("Assistant reported: " + line)
    return items[-12:]


def extract_changed_files(text: str) -> list[str]:
    def clean(path: str) -> str:
        cleaned = path.strip().rstrip(".,)")
        return cleaned

    latest_reported: list[str] = []
    for _, body in transcript_messages(text):
        marker = re.search(r"Changed (?:in this pass|files):", body, re.IGNORECASE)
        if not marker:
            continue
        block = re.split(r"\n(?:Verification|Tests|Next|For the next)\b", body[marker.end() :], maxsplit=1)[0]
        current: list[str] = []
        for match in re.finditer(r"\[[^\]]+\]\((?P<path>/[^)]+|[^)]+\.[A-Za-z0-9_+-]+)\)", block):
            current.append(clean(match.group("path")))
        for match in re.finditer(r"^- `?(?P<path>(?:/|[\w.-]+/)[\w./ @+-]+\.[A-Za-z0-9_+-]+)`?", block, re.MULTILINE):
            current.append(clean(match.group("path")))
        if current:
            latest_reported = current
    if latest_reported:
        return list(dict.fromkeys(path for path in latest_reported if path))[:24]

    patch_paths = [clean(match.group("path")) for match in PATCH_PATH_RE.finditer(text)]
    return list(dict.fromkeys(path for path in patch_paths[-24:] if path))[:24]


def extract_verification(text: str) -> list[str]:
    checks: list[str] = []
    seen: set[str] = set()

    def add(line: str) -> None:
        cleaned = re.sub(r"\s+", " ", line.strip().lstrip("- ").strip("`"))
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            checks.append(cleaned)

    latest_block: str | None = None
    for _, body in transcript_messages(text):
        marker = re.search(r"Verification:", body, re.IGNORECASE)
        if marker:
            latest_block = re.split(r"\n(?:Note|For the next|Next)\b", body[marker.end() :], maxsplit=1)[0]
    if latest_block:
        for line in latest_block.splitlines():
            if line.strip().endswith("?"):
                continue
            if "passed" in line.lower() or "ok:" in line.lower() or "smoke" in line.lower():
                add(line)
    if not checks:
        for match in re.finditer(r"\b\d+ passed[^\n`]*", text):
            add(match.group(0))
    return checks[:8]


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
    summary = compact_summary(transcript_text)
    changed_files = extract_changed_files(transcript_text)
    verification = extract_verification(transcript_text)
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
{format_list(summary, max_items=12, max_chars=1000) if summary else "- No authored/recent user-assistant summary captured."}

## 3. What in-progress
- {plan or "Inspect repo state, retrieve narrowly, then execute verified steps."}

## 4. What next
- Read this handoff and `start.md` if present only.
- Verify this is a fresh successor context.
- Build plan before execution.

## 5. Key files touched
{format_list(changed_files, max_items=12, max_chars=220) if changed_files else "- none captured; ask old only if exact files are needed and repo retrieval is insufficient"}

## 6. Key decisions
{format_list(facts["decisions"])}

## Verification Seen
{format_list(verification, max_items=6, max_chars=220)}

## 7. Retrieval pointers
{start_pointer}
- Ask old only for a specific missing fact after repo retrieval is insufficient.

## 8. Open questions
- none captured

## 9. Instructions for next agent
- Start in plan mode. Think step-by-step. Create a compact plan before executing.
- Do not load broad archives until retrieval proves relevance.
- Narrow repo retrieval means targeted reads/searches of known files, status, or symbols; it does not mean loading broad archives.
- If a needed fact is absent and repo retrieval is insufficient, ask the old session explicitly:
  `python3 -m relay_session.cli ask-old --handoff <handoff-file> --question "<specific missing fact>"`
- Omit `--execute` to dry-run old-session routing; add `--execute` to actually ask the old session.
- If the old session identifies an even older relay handoff as the source, repeat `ask-old` with that older handoff and the same narrow question.
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
