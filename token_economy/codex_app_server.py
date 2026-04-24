from __future__ import annotations

import json
import os
import select
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_CODEX_FRESH_MODEL = "gpt-5.3-codex-spark"


def default_codex_fresh_model() -> str:
    return os.environ.get("TOKEN_ECONOMY_CODEX_FRESH_MODEL") or os.environ.get("CODEX_MODEL") or DEFAULT_CODEX_FRESH_MODEL


def build_successor_prompt(repo_root: Path, handoff: Path) -> str:
    return (
        f"Read {repo_root}/start.md and {handoff} only. Continue from that handoff. "
        "Do not load broad wiki/raw archives until retrieval proves relevance. "
        "Start in plan mode. First report that this is a fresh successor context, then verify the handoff and stop."
    )


def codex_fresh_thread_plan(repo_root: Path, handoff: Path, model: str | None = None) -> dict[str, Any]:
    model_name = model or default_codex_fresh_model()
    prompt = build_successor_prompt(repo_root, handoff)
    return {
        "agent": "codex",
        "mode": "app-server-fresh-thread",
        "model": model_name,
        "repo_root": str(repo_root),
        "handoff": str(handoff),
        "prompt": prompt,
        "command": f'./te context codex-fresh-thread --handoff "{handoff}" --model "{model_name}" --execute',
        "success_test": [
            "App Server emits thread/started with turns: [] and the requested cwd.",
            "A turn/start succeeds in that new thread.",
            "The assistant responds from the new thread and the thread returns to idle.",
        ],
        "note": "This creates a fresh successor Codex thread. It does not erase the old host transcript.",
    }


def _send(proc: subprocess.Popen[str], obj: dict[str, Any]) -> None:
    assert proc.stdin is not None
    proc.stdin.write(json.dumps(obj) + "\n")
    proc.stdin.flush()


def _read_events(proc: subprocess.Popen[str], timeout: float) -> list[dict[str, Any]]:
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
            events.append(json.loads(line))
        except json.JSONDecodeError:
            events.append({"raw": line.rstrip("\n")})
    return events


def _find_response(events: list[dict[str, Any]], request_id: int) -> dict[str, Any] | None:
    for event in events:
        if event.get("id") == request_id:
            return event
    return None


def _assistant_responded(events: list[dict[str, Any]]) -> bool:
    for event in events:
        params = event.get("params") or {}
        item = params.get("item") or {}
        if item.get("type") == "agentMessage":
            return True
        delta = params.get("delta") or ""
        if isinstance(delta, str) and delta.strip():
            return True
    return False


def _thread_idle(events: list[dict[str, Any]], thread_id: str | None) -> bool:
    for event in reversed(events):
        if event.get("method") != "thread/status/changed":
            continue
        params = event.get("params") or {}
        if thread_id and params.get("threadId") != thread_id:
            continue
        status = params.get("status") or {}
        return status.get("type") == "idle"
    return False


def _thread_started_info(events: list[dict[str, Any]], thread_id: str | None) -> dict[str, Any]:
    for event in events:
        if event.get("method") != "thread/started":
            continue
        thread = (event.get("params") or {}).get("thread") or {}
        if thread_id and thread.get("id") != thread_id:
            continue
        return {
            "thread_ephemeral": bool(thread.get("ephemeral")),
            "thread_turns_empty": thread.get("turns") == [],
            "thread_source": thread.get("source"),
            "thread_cwd": thread.get("cwd"),
        }
    return {"thread_ephemeral": False, "thread_turns_empty": False, "thread_source": None, "thread_cwd": None}


def _latest_token_usage(events: list[dict[str, Any]], thread_id: str | None) -> dict[str, Any]:
    for event in reversed(events):
        if event.get("method") != "thread/tokenUsage/updated":
            continue
        params = event.get("params") or {}
        if thread_id and params.get("threadId") != thread_id:
            continue
        usage = params.get("tokenUsage") or {}
        last = usage.get("last") or {}
        total = usage.get("total") or {}
        return {
            "model_context_window": usage.get("modelContextWindow"),
            "last_input_tokens": last.get("inputTokens"),
            "last_total_tokens": last.get("totalTokens"),
            "cumulative_total_tokens": total.get("totalTokens"),
        }
    return {
        "model_context_window": None,
        "last_input_tokens": None,
        "last_total_tokens": None,
        "cumulative_total_tokens": None,
    }


def run_codex_fresh_thread(repo_root: Path, handoff: Path, model: str | None = None, timeout: int = 120) -> dict[str, Any]:
    plan = codex_fresh_thread_plan(repo_root, handoff, model)
    outdir = repo_root / ".token-economy" / "checkpoints" / "codex-app-server" / datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    outdir.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(
        ["codex", "app-server", "--listen", "stdio://"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    all_events: list[dict[str, Any]] = []
    stderr_text = ""
    thread_id: str | None = None
    try:
        _send(
            proc,
            {
                "id": 1,
                "method": "initialize",
                "params": {
                    "clientInfo": {"name": "token-economy", "title": "Token Economy Fresh Thread", "version": "0.1.0"},
                    "capabilities": {"experimentalApi": True},
                },
            },
        )
        all_events.extend(_read_events(proc, 5))
        _send(proc, {"method": "initialized", "params": {}})
        _send(
            proc,
            {
                "id": 2,
                "method": "thread/start",
                "params": {
                    "cwd": str(repo_root),
                    "approvalPolicy": "never",
                    "sandbox": "workspace-write",
                    "ephemeral": True,
                    "model": plan["model"],
                },
            },
        )
        all_events.extend(_read_events(proc, 10))
        thread_response = _find_response(all_events, 2)
        try:
            thread_id = thread_response["result"]["thread"]["id"] if thread_response else None
        except (KeyError, TypeError):
            thread_id = None
        if thread_id:
            _send(
                proc,
                {
                    "id": 3,
                    "method": "turn/start",
                    "params": {
                        "threadId": thread_id,
                        "input": [{"type": "text", "text": plan["prompt"]}],
                        "approvalPolicy": "never",
                        "model": plan["model"],
                    },
                },
            )
            all_events.extend(_read_events(proc, timeout))
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        if proc.stderr is not None:
            stderr_text = proc.stderr.read()

    events_path = outdir / "events.jsonl"
    events_path.write_text("\n".join(json.dumps(event, sort_keys=True) for event in all_events) + "\n", encoding="utf-8")
    stderr_path = outdir / "stderr.txt"
    stderr_path.write_text(stderr_text, encoding="utf-8")
    summary = {
        **plan,
        "thread_id": thread_id,
        **_thread_started_info(all_events, thread_id),
        "assistant_responded": _assistant_responded(all_events),
        "thread_idle": _thread_idle(all_events, thread_id),
        **_latest_token_usage(all_events, thread_id),
        "ok": bool(thread_id and _assistant_responded(all_events) and _thread_idle(all_events, thread_id)),
        "events": str(events_path),
        "stderr": str(stderr_path),
    }
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary
