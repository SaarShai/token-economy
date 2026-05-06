from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from math import ceil
from pathlib import Path
from typing import Any


PATH_RE = re.compile(r"(?P<path>(?:/|\.{1,2}/|[\w.-]+/)[\w./ @+-]+\.[A-Za-z0-9_+-]+)")
PATCH_PATH_RE = re.compile(r"^\*\*\* (?:Update|Add|Delete) File: (?P<path>.+)$", re.MULTILINE)
CMD_RE = re.compile(r"(?:cmd|command|bash|shell)[\"': ]+([^\\n]{3,240})", re.IGNORECASE)
ERR_RE = re.compile(r"((?:error|exception|traceback|failed|fatal)[^\n]{0,240})", re.IGNORECASE)
RELAY_NAME_RE = re.compile(r"^Relay\[(?P<version>\d+)\]:\s*(?P<name>.+)$")
SECTION_RE = re.compile(
    r"^\s*(?P<title>Changed files|Verification|Tests|Conclusion|Conclusions|Confirmed|Decisions|Key decisions|Current safe state|Open questions|Next|What next)\s*:\s*$",
    re.IGNORECASE | re.MULTILINE,
)


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
    errors: list[str] = []
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
            if ERR_RE.search(line):
                cleaned = re.sub(r"\s+", " ", line.strip().lstrip("- ").strip("`"))
                if cleaned and cleaned not in errors:
                    errors.append(cleaned)
    return {"files": [], "commands": [], "errors": errors[:4], "decisions": decisions[:8]}


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


def _strip_bullet(line: str) -> str:
    return re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", line.strip()).strip("` ")


def _dedupe(items: list[str], limit: int | None = None) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        clean = re.sub(r"\s+", " ", item).strip()
        if clean and clean not in seen:
            seen.add(clean)
            result.append(clean)
            if limit and len(result) >= limit:
                break
    return result


def _structured_blocks(body: str) -> dict[str, list[str]]:
    matches = list(SECTION_RE.finditer(body))
    blocks: dict[str, list[str]] = {}
    for index, match in enumerate(matches):
        title = match.group("title").lower()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        lines = []
        for raw in body[start:end].splitlines():
            line = _strip_bullet(raw)
            if not line or len(line) < 4:
                continue
            if line.startswith("```"):
                continue
            lines.append(line)
        if lines:
            blocks.setdefault(title, []).extend(lines)
    return blocks


def extract_structured_summary(text: str) -> dict[str, list[str]]:
    facts: list[str] = []
    decisions: list[str] = []
    next_steps: list[str] = []
    open_questions: list[str] = []
    fallback: list[str] = []

    fact_re = re.compile(
        r"\b(proven conclusion|conclusion|confirmed|fixed|regression boundary|safe state|current safe state|backend|sidebar|ui visibility|listed_after_start|reverted|restored|commit|pushed|installed|launched)\b",
        re.IGNORECASE,
    )
    decision_re = re.compile(r"\b(should|should not|must|do not|avoid|keep|treat|only|priority|assumption)\b", re.IGNORECASE)
    messages = transcript_messages(text)

    for role, body in messages[-24:]:
        if role == "assistant":
            blocks = _structured_blocks(body)
            for key, lines in blocks.items():
                if key in {"conclusion", "conclusions", "confirmed", "current safe state"}:
                    facts.extend(lines)
                elif key in {"decisions", "key decisions"}:
                    decisions.extend(lines)
                elif key in {"next", "what next"}:
                    next_steps.extend(lines)
                elif key == "open questions":
                    open_questions.extend(lines)
            for raw in body.splitlines():
                line = _strip_bullet(raw)
                if not line or line.endswith(":") or len(line) < 8:
                    continue
                if fact_re.search(line):
                    facts.append(line)
                elif decision_re.search(line):
                    decisions.append(line)
        elif role == "user":
            first = body.splitlines()[0].strip()
            if first:
                fallback.append("User request: " + first)

    if not facts:
        facts = fallback[-4:]
    return {
        "facts": _dedupe(facts, 10),
        "decisions": _dedupe(decisions, 8),
        "next": _dedupe(next_steps, 4),
        "open_questions": _dedupe([q for q in open_questions if q.lower() not in {"none", "none captured"}], 4),
    }


def compact_summary(text: str) -> list[str]:
    structured = extract_structured_summary(text)
    return structured["facts"][:12]


def current_git_state(repo_root: Path) -> list[str]:
    def run(args: list[str]) -> str:
        try:
            return subprocess.check_output(args, cwd=repo_root, stderr=subprocess.DEVNULL, text=True, timeout=3).strip()
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return ""

    inside = run(["git", "rev-parse", "--is-inside-work-tree"])
    if inside != "true":
        return ["not a git worktree"]
    branch = run(["git", "branch", "--show-current"]) or "detached"
    head = run(["git", "rev-parse", "--short", "HEAD"]) or "unknown"
    status = run(["git", "status", "--short"])
    dirty = len([line for line in status.splitlines() if line.strip()])
    return [f"HEAD {head} on {branch}", f"dirty entries: {dirty}"]


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
            if re.search(r"\b(passed|ok:|smoke|appeared|visible|listed|launched|restored)\b", line, re.IGNORECASE):
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


def _handoff_quality(text: str, max_tokens: int) -> dict[str, Any]:
    required = [
        "old-session-query-policy: explicit-only",
        "old-thread-id:",
        "old-transcript:",
        "## 1. Current task",
        "## 2. Context packet",
        "## 9. Instructions for next agent",
        "Layer 1:",
        "Layer 2:",
        "Layer 3:",
        "Layer 4:",
        "Omit `--execute`",
        "add `--execute`",
        "even older relay handoff",
    ]
    missing = [item for item in required if item not in text]
    warnings: list[str] = []
    if re.search(r"\b(User asked|Assistant reported):", text):
        warnings.append("transcript-style summary fragments present")
    if re.search(r"(?<!Do not )load broad archives", text, re.IGNORECASE):
        warnings.append("broad archive instruction is ambiguous")
    command_section = re.search(r"## Commands Seen\n(?P<body>.*?)(?:\n## |\Z)", text, re.DOTALL)
    if command_section and len([line for line in command_section.group("body").splitlines() if line.strip().startswith("-")]) > 4:
        warnings.append("too many command bullets")
    tokens = estimate_tokens(text)
    return {
        "tokens": tokens,
        "max_tokens": max_tokens,
        "missing": missing,
        "warnings": warnings,
        "ok": not missing and not warnings and tokens <= max_tokens,
    }


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
    structured = extract_structured_summary(transcript_text)
    summary = structured["facts"]
    decisions = _dedupe(structured["decisions"] + facts["decisions"], 8)
    changed_files = extract_changed_files(transcript_text)
    verification = extract_verification(transcript_text)
    next_steps = structured["next"]
    open_questions = structured["open_questions"]
    git_state = current_git_state(repo_root)
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

## 2. Context packet
### Proven facts
{format_list(summary, max_items=10, max_chars=260) if summary else "- none captured; retrieve narrowly before asking old"}

### Recent decisions
{format_list(decisions, max_items=8, max_chars=220)}

### Changed files
{format_list(changed_files, max_items=12, max_chars=220) if changed_files else "- none captured; ask old only if exact files are needed and repo retrieval is insufficient"}

### Verification seen
{format_list(verification, max_items=6, max_chars=220)}

### Current git state
{format_list(git_state, max_items=4, max_chars=180)}

### UI/session access notes
- `Backend listing proves session creation; Codex Desktop sidebar visibility can lag. Restart Codex to refresh if needed.`
- `If the relay is backend-listed but hidden in the sidebar, use codex resume <thread-id> if a thread id is available.`

## 3. What in-progress
- {plan or "Inspect repo state, retrieve narrowly, then execute verified steps."}

## 4. What next
- {next_steps[0] if next_steps else "Read this handoff and `start.md` if present only."}
- Verify this is a fresh successor context.
- Build plan before execution.

## 5. Key files touched
- See `### Changed files` in the context packet.

## 6. Key decisions
- See `### Recent decisions` in the context packet.

## Verification Seen
- See `### Verification seen` in the context packet.

## 7. Retrieval pointers
{start_pointer}
- Layer 1: read `start.md` plus this handoff only.
- Layer 2: use narrow repo retrieval against known files, `rg`, `git status`, and focused tests.
- Layer 3: if a needed fact is still absent, ask old with `ask-old --handoff <file> --question "<specific missing fact>"`.
- Layer 4: if the old session identifies an even older relay handoff as the source, repeat `ask-old` with that older handoff and the same narrow question.

## 8. Open questions
{format_list(open_questions, max_items=4, max_chars=220)}

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
    if estimate_tokens(packet) > max_packet_tokens:
        packet = packet.replace(format_list(decisions), format_list(decisions, max_items=4, max_chars=160))
        packet = packet.replace(format_list(summary, max_items=10, max_chars=260), format_list(summary, max_items=6, max_chars=180))
    path = state_dir / f"{ts}-fresh-session.md"
    path.write_text(packet, encoding="utf-8")
    quality = _handoff_quality(packet, max_packet_tokens)
    return {"path": str(path), "tokens": estimate_tokens(packet), "packet": packet, "quality": quality}


def lint_handoff(path: Path, max_tokens: int = 2000) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    quality = _handoff_quality(text, max_tokens)
    return {"path": str(path), **quality}


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
