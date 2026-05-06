from __future__ import annotations

import json
import os
import select
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


DEFAULT_MODEL = "gpt-5.5"


def default_model() -> str:
    return os.environ.get("RELAY_SESSION_CODEX_MODEL") or os.environ.get("CODEX_MODEL") or DEFAULT_MODEL


def _send(proc: subprocess.Popen[str], obj: dict[str, Any]) -> None:
    assert proc.stdin is not None
    proc.stdin.write(json.dumps(obj) + "\n")
    proc.stdin.flush()


def _read_until(proc: subprocess.Popen[str], timeout: float, pred: Callable[[list[dict[str, Any]], dict[str, Any]], bool]) -> list[dict[str, Any]]:
    assert proc.stdout is not None
    deadline = time.time() + timeout
    events: list[dict[str, Any]] = []
    while time.time() < deadline:
        ready, _, _ = select.select([proc.stdout], [], [], 0.2)
        if not ready:
            if proc.poll() is not None:
                break
            continue
        line = proc.stdout.readline()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            event = {"raw": line.rstrip("\n")}
        events.append(event)
        if pred(events, event):
            break
    return events


def _response(events: list[dict[str, Any]], request_id: int) -> dict[str, Any] | None:
    return next((event for event in events if event.get("id") == request_id), None)


def _assistant_responded(events: list[dict[str, Any]]) -> bool:
    for event in events:
        params = event.get("params") or {}
        item = params.get("item") or {}
        if item.get("type") == "agentMessage":
            return True
        if isinstance(params.get("delta"), str) and params["delta"].strip():
            return True
    return False


def _idle(events: list[dict[str, Any]], thread_id: str | None) -> bool:
    for event in reversed(events):
        if event.get("method") != "thread/status/changed":
            continue
        params = event.get("params") or {}
        if thread_id and params.get("threadId") != thread_id:
            continue
        return ((params.get("status") or {}).get("type")) == "idle"
    return False


def _turn_completed(events: list[dict[str, Any]], thread_id: str | None) -> bool:
    for event in reversed(events):
        if event.get("method") != "turn/completed":
            continue
        params = event.get("params") or {}
        if thread_id and params.get("threadId") != thread_id:
            continue
        return True
    return False


def _thread_started_info(events: list[dict[str, Any]], thread_id: str | None) -> dict[str, Any]:
    for event in events:
        if event.get("method") != "thread/started":
            continue
        thread = (event.get("params") or {}).get("thread") or {}
        if thread_id and thread.get("id") != thread_id:
            continue
        return {
            "thread_persistent": thread.get("ephemeral") is False,
            "thread_turns_empty": thread.get("turns") == [],
            "thread_source": thread.get("source"),
            "thread_cwd": thread.get("cwd"),
        }
    return {"thread_persistent": False, "thread_turns_empty": False, "thread_source": None, "thread_cwd": None}


def _listed_info(events: list[dict[str, Any]], request_id: int, thread_id: str | None) -> dict[str, Any]:
    response = _response(events, request_id)
    data = ((response or {}).get("result") or {}).get("data") or []
    ids = [thread.get("id") for thread in data if isinstance(thread, dict)]
    listed = next((thread for thread in data if isinstance(thread, dict) and thread.get("id") == thread_id), None)
    return {"listed_after_start": bool(thread_id and thread_id in ids), "listed_count": len(data), "listed_name": (listed or {}).get("name")}


def successor_prompt(repo_root: Path, handoff: Path, session_name: str | None, continue_work: bool) -> str:
    title = f"{session_name}\n\n" if session_name else ""
    name_text = f'This relay session is named "{session_name}". ' if session_name else ""
    ending = "verify the handoff, then continue from where the older session left off." if continue_work else "verify the handoff and stop."
    start = repo_root / "start.md"
    start_text = f"Read {start} and {handoff} only." if start.exists() else f"Read {handoff} only."
    return (
        f"{title}{start_text} Continue from that handoff. {name_text}"
        "Do not load broad archives until retrieval proves relevance. "
        "If a needed fact is absent and repo retrieval is insufficient, use `python3 -m relay_session.cli ask-old --handoff <handoff-file> --question \"<specific missing fact>\"`. "
        f"Start in plan mode. First report that this is a fresh successor context, {ending}"
    )


def run_fresh_thread(repo_root: Path, handoff: Path, session_name: str | None, model: str | None = None, timeout: int = 120, continue_work: bool = True) -> dict[str, Any]:
    model_name = (model or default_model()).strip().replace(" ", "-")
    prompt = successor_prompt(repo_root, handoff, session_name, continue_work)
    outdir = repo_root / ".relay-session" / "codex-app-server" / datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    outdir.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(["codex", "app-server", "--listen", "stdio://"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
    events: list[dict[str, Any]] = []
    stderr_text = ""
    thread_id = None
    set_name_request_id = 4
    list_request_id = 5
    try:
        _send(proc, {"id": 1, "method": "initialize", "params": {"clientInfo": {"name": "relay-session", "title": "Relay Session", "version": "0.1.0"}, "capabilities": {"experimentalApi": True}}})
        events.extend(_read_until(proc, 5, lambda _events, event: event.get("id") == 1))
        _send(proc, {"method": "initialized", "params": {}})
        params: dict[str, Any] = {"cwd": str(repo_root), "approvalPolicy": "never", "sandbox": "workspace-write", "ephemeral": False, "model": model_name}
        _send(proc, {"id": 2, "method": "thread/start", "params": params})
        start_events = _read_until(proc, 10, lambda _events, event: event.get("id") == 2)
        events.extend(start_events)
        response = _response(start_events, 2)
        thread_id = (((response or {}).get("result") or {}).get("thread") or {}).get("id")
        if thread_id:
            if session_name:
                _send(proc, {"id": set_name_request_id, "method": "thread/name/set", "params": {"threadId": thread_id, "name": session_name}})
                events.extend(_read_until(proc, 8, lambda _events, event: event.get("id") == set_name_request_id or event.get("method") == "thread/name/updated"))
            _send(proc, {"id": 3, "method": "turn/start", "params": {"threadId": thread_id, "input": [{"type": "text", "text": prompt}], "approvalPolicy": "never", "model": model_name}})
            events.extend(_read_until(proc, timeout, lambda seen, event: (_assistant_responded(seen) and _idle(seen, thread_id)) or _turn_completed(seen, thread_id) or bool(event.get("method") == "error" and not event.get("willRetry"))))
            _send(proc, {"id": list_request_id, "method": "thread/list", "params": {"cwd": str(repo_root), "archived": False, "limit": 20, "sourceKinds": ["cli", "vscode", "exec", "appServer", "unknown"], "sortKey": "updated_at"}})
            events.extend(_read_until(proc, 8, lambda _events, event: event.get("id") == list_request_id))
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        if proc.stderr is not None:
            stderr_text = proc.stderr.read()
    events_path = outdir / "events.jsonl"
    events_path.write_text("\n".join(json.dumps(event, sort_keys=True) for event in events) + "\n", encoding="utf-8")
    (outdir / "stderr.txt").write_text(stderr_text, encoding="utf-8")
    started_info = _thread_started_info(events, thread_id)
    listed_info = _listed_info(events, list_request_id, thread_id)
    ok = bool(
        thread_id
        and _assistant_responded(events)
        and _idle(events, thread_id)
        and started_info["thread_persistent"]
        and started_info["thread_turns_empty"]
        and listed_info["listed_after_start"]
    )
    return {
        "ok": ok,
        "thread_id": thread_id,
        "session_name": session_name,
        "thread_named": not session_name or listed_info.get("listed_name") == session_name,
        "model": model_name,
        "assistant_responded": _assistant_responded(events),
        "thread_idle": _idle(events, thread_id),
        **started_info,
        **listed_info,
        "events": str(events_path),
    }


def run_ask_old(repo_root: Path, thread_id: str, question: str, model: str | None = None, timeout: int = 120) -> dict[str, Any]:
    model_name = (model or default_model()).strip().replace(" ", "-")
    prompt = "Answer only this specific relay follow-up from your old session context. Cite source if possible. Do not continue implementation. Question: " + question
    outdir = repo_root / ".relay-session" / "codex-app-server-ask-old" / datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    outdir.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(["codex", "app-server", "--listen", "stdio://"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
    events: list[dict[str, Any]] = []
    stderr_text = ""
    try:
        _send(proc, {"id": 1, "method": "initialize", "params": {"clientInfo": {"name": "relay-session", "title": "Relay Ask Old", "version": "0.1.0"}, "capabilities": {"experimentalApi": True}}})
        events.extend(_read_until(proc, 5, lambda _events, event: event.get("id") == 1))
        _send(proc, {"method": "initialized", "params": {}})
        _send(proc, {"id": 2, "method": "thread/resume", "params": {"threadId": thread_id, "cwd": str(repo_root), "approvalPolicy": "never", "sandbox": "workspace-write", "model": model_name}})
        events.extend(_read_until(proc, 15, lambda _events, event: event.get("id") == 2 or event.get("method") == "thread/started"))
        _send(proc, {"id": 3, "method": "turn/start", "params": {"threadId": thread_id, "input": [{"type": "text", "text": prompt}], "approvalPolicy": "never", "model": model_name}})
        events.extend(_read_until(proc, timeout, lambda seen, event: (_assistant_responded(seen) and _idle(seen, thread_id)) or event.get("method") == "turn/completed"))
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        if proc.stderr is not None:
            stderr_text = proc.stderr.read()
    events_path = outdir / "events.jsonl"
    events_path.write_text("\n".join(json.dumps(event, sort_keys=True) for event in events) + "\n", encoding="utf-8")
    (outdir / "stderr.txt").write_text(stderr_text, encoding="utf-8")
    answers = [((event.get("params") or {}).get("item") or {}).get("text") for event in events if ((event.get("params") or {}).get("item") or {}).get("type") == "agentMessage"]
    return {"ok": bool(_assistant_responded(events)), "mode": "codex-old-thread", "thread_id": thread_id, "question": question, "answer": "\n".join(answer for answer in answers if answer), "events": str(events_path)}
