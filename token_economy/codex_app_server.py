from __future__ import annotations

import json
import os
import select
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


DEFAULT_CODEX_FRESH_MODEL = "gpt-5.5"


def default_codex_fresh_model() -> str:
    return os.environ.get("TOKEN_ECONOMY_CODEX_FRESH_MODEL") or os.environ.get("CODEX_MODEL") or DEFAULT_CODEX_FRESH_MODEL


def codex_fresh_model_name(model: str | None = None) -> str:
    return (model or default_codex_fresh_model()).strip().replace(" ", "-")


def build_successor_prompt(repo_root: Path, handoff: Path, session_name: str | None = None, continue_work: bool = False) -> str:
    title = f"{session_name}\n\n" if session_name else ""
    name_text = f'This relay session is named "{session_name}". ' if session_name else ""
    ending = (
        "First report that this is a fresh successor context, verify the handoff, then continue from where the older session left off."
        if continue_work
        else "First report that this is a fresh successor context, then verify the handoff and stop."
    )
    return (
        f"{title}"
        f"Read {repo_root}/start.md and {handoff} only. Continue from that handoff. "
        f"{name_text}"
        "Do not load broad wiki/raw archives until retrieval proves relevance. "
        "If a needed fact is absent and repo/wiki retrieval is insufficient, use `./te context ask-old --handoff <handoff-file> --question \"<specific missing fact>\"`. "
        f"Start in plan mode. {ending}"
    )


def build_compact_prompt(repo_root: Path, handoff: Path | None = None) -> str:
    handoff_text = f" Use this handoff as the source of truth: {handoff}." if handoff else ""
    return (
        "Compact this Codex thread for Token Economy continuation. Preserve only the lean continuation state: "
        "current goal, exact repo root, exact files touched, commands run, errors/blockers, decisions and rationale, "
        "commits/push state, active subagents that are not completed, and next actions. "
        "Exclude transcript noise, raw logs, broad wiki pages, and docs-only discoveries. "
        "Mention durable wiki/log pages by path instead of loading their contents. "
        f"After compaction, continue with only {repo_root}/start.md plus the compacted handoff-worthy summary; "
        "retrieve more only when relevance is proven."
        f"{handoff_text}"
    )


def codex_fresh_thread_plan(
    repo_root: Path,
    handoff: Path,
    model: str | None = None,
    ephemeral: bool = False,
    session_name: str | None = None,
    continue_work: bool = False,
) -> dict[str, Any]:
    model_name = codex_fresh_model_name(model)
    prompt = build_successor_prompt(repo_root, handoff, session_name=session_name, continue_work=continue_work)
    persistence = "ephemeral" if ephemeral else "persistent"
    return {
        "agent": "codex",
        "mode": "app-server-fresh-thread",
        "model": model_name,
        "launch_model": None,
        "turn_model": model_name,
        "model_candidates": [model_name],
        "session_name": session_name,
        "continue_work": continue_work,
        "persistence": persistence,
        "repo_root": str(repo_root),
        "handoff": str(handoff),
        "prompt": prompt,
        "command": f'./te context codex-fresh-thread --handoff "{handoff}" --model "{model_name}" --execute' + (" --ephemeral" if ephemeral else ""),
        "success_test": [
            f"App Server emits thread/started with turns: [] and {persistence} state in the requested cwd.",
            "The thread is created with the requested model before the first turn starts.",
            "A turn/start succeeds in that new thread.",
            "The assistant responds from the new thread and the thread returns to idle.",
            "For persistent mode, thread/list can find the new thread by exact cwd.",
        ],
        "note": "This creates a fresh successor Codex thread in the same project. It does not erase the old host transcript.",
    }


def codex_compact_thread_plan(repo_root: Path, thread_id: str | None = None, handoff: Path | None = None, model: str | None = None) -> dict[str, Any]:
    target_thread = thread_id or os.environ.get("CODEX_THREAD_ID")
    compact_prompt = build_compact_prompt(repo_root, handoff)
    model_name = model or default_codex_fresh_model()
    return {
        "agent": "codex",
        "mode": "app-server-thread-compact",
        "status": "experimental-current-thread-clear-unsolved",
        "model": model_name,
        "repo_root": str(repo_root),
        "thread_id": target_thread,
        "handoff": str(handoff) if handoff else None,
        "compact_prompt": compact_prompt,
        "command": "./te context codex-compact-thread --current --execute"
        if thread_id is None
        else f'./te context codex-compact-thread --thread-id "{thread_id}" --execute',
        "success_test": [
            "App Server resumes the target thread with the custom compact_prompt override.",
            "thread/compact/start is accepted for that thread.",
            "App Server emits thread/compacted for the same thread id.",
        ],
        "note": "Experimental only. Codex current-thread clear/compact is unsolved in the tested Desktop/App Server environment; prefer codex-fresh-thread for clean continuation.",
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


def _read_events_until(
    proc: subprocess.Popen[str],
    timeout: float,
    predicate: Callable[[list[dict[str, Any]], dict[str, Any]], bool],
) -> list[dict[str, Any]]:
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
        if predicate(events, event):
            break
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
            "thread_ephemeral": bool(thread.get("ephemeral")),
            "thread_persistent": thread.get("ephemeral") is False,
            "thread_turns_empty": thread.get("turns") == [],
            "thread_source": thread.get("source"),
            "thread_cwd": thread.get("cwd"),
            "thread_path": thread.get("path"),
        }
    return {"thread_ephemeral": False, "thread_persistent": False, "thread_turns_empty": False, "thread_source": None, "thread_cwd": None, "thread_path": None}


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


def _listed_info(events: list[dict[str, Any]], request_id: int, thread_id: str | None) -> dict[str, Any]:
    response = _find_response(events, request_id)
    data = ((response or {}).get("result") or {}).get("data") or []
    ids = [thread.get("id") for thread in data if isinstance(thread, dict)]
    return {"listed_after_start": bool(thread_id and thread_id in ids), "listed_count": len(data)}


def run_codex_ask_old_thread(repo_root: Path, thread_id: str, question: str, model: str | None = None, timeout: int = 120) -> dict[str, Any]:
    model_name = model or default_codex_fresh_model()
    prompt = (
        "Answer only this specific relay follow-up from your old session context. "
        "Cite the source from old context when possible. Do not continue implementation. "
        f"Question: {question}"
    )
    outdir = repo_root / ".token-economy" / "checkpoints" / "codex-app-server-ask-old" / datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
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
    try:
        _send(proc, {"id": 1, "method": "initialize", "params": {"clientInfo": {"name": "token-economy", "title": "Token Economy Ask Old", "version": "0.1.0"}, "capabilities": {"experimentalApi": True}}})
        all_events.extend(_read_events_until(proc, 5, lambda events, event: event.get("id") == 1))
        _send(proc, {"method": "initialized", "params": {}})
        _send(proc, {"id": 2, "method": "thread/resume", "params": {"threadId": thread_id, "cwd": str(repo_root), "approvalPolicy": "never", "sandbox": "workspace-write", "model": model_name}})
        all_events.extend(_read_events_until(proc, 15, lambda events, event: event.get("id") == 2 or event.get("method") == "thread/started"))
        _send(proc, {"id": 3, "method": "turn/start", "params": {"threadId": thread_id, "input": [{"type": "text", "text": prompt}], "approvalPolicy": "never", "model": model_name}})
        all_events.extend(_read_events_until(proc, timeout, lambda events, event: bool(_assistant_responded(events) and _thread_idle(events, thread_id)) or bool(event.get("method") == "error" and not event.get("willRetry"))))
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
    answers = [
        ((event.get("params") or {}).get("item") or {}).get("text")
        for event in all_events
        if ((event.get("params") or {}).get("item") or {}).get("type") == "agentMessage"
    ]
    return {
        "ok": bool(_assistant_responded(all_events) and _thread_idle(all_events, thread_id)),
        "mode": "codex-old-thread",
        "thread_id": thread_id,
        "question": question,
        "answer": "\n".join(answer for answer in answers if answer),
        "events": str(events_path),
        "stderr": str(stderr_path),
    }


def run_codex_fresh_thread(
    repo_root: Path,
    handoff: Path,
    model: str | None = None,
    timeout: int = 120,
    ephemeral: bool = False,
    session_name: str | None = None,
    continue_work: bool = False,
) -> dict[str, Any]:
    plan = codex_fresh_thread_plan(repo_root, handoff, model, ephemeral=ephemeral, session_name=session_name, continue_work=continue_work)
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
    list_request_id: int | None = None
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
        all_events.extend(_read_events_until(proc, 5, lambda events, event: event.get("id") == 1))
        _send(proc, {"method": "initialized", "params": {}})
        turn_model = plan["turn_model"]
        thread_request_id = 2
        turn_request_id = 3
        list_request_id = 4
        thread_start_params = {
            "cwd": str(repo_root),
            "approvalPolicy": "never",
            "sandbox": "workspace-write",
            "ephemeral": ephemeral,
            "model": turn_model,
        }
        if session_name:
            thread_start_params["name"] = session_name
        _send(
            proc,
            {
                "id": thread_request_id,
                "method": "thread/start",
                "params": thread_start_params,
            },
        )
        start_events = _read_events_until(proc, 10, lambda events, event: event.get("id") == thread_request_id)
        all_events.extend(start_events)
        thread_response = _find_response(start_events, thread_request_id)
        try:
            thread_id = thread_response["result"]["thread"]["id"] if thread_response else None
        except (KeyError, TypeError):
            thread_id = None
        if thread_id:
            _send(
                proc,
                {
                    "id": turn_request_id,
                    "method": "turn/start",
                    "params": {
                        "threadId": thread_id,
                        "input": [{"type": "text", "text": plan["prompt"]}],
                        "approvalPolicy": "never",
                        "model": turn_model,
                    },
                },
            )
            all_events.extend(
                _read_events_until(
                    proc,
                    timeout,
                    lambda events, event: bool(_assistant_responded(events) and _thread_idle(events, thread_id))
                    or bool(_turn_completed(events, thread_id))
                    or bool(event.get("method") == "error" and not event.get("willRetry")),
                )
            )
            if _assistant_responded(all_events) and _thread_idle(all_events, thread_id):
                plan["launch_model"] = turn_model
        if thread_id and not ephemeral:
            list_request_id = (list_request_id or 2) + 1000
            _send(
                proc,
                {
                    "id": list_request_id,
                    "method": "thread/list",
                    "params": {
                        "cwd": str(repo_root),
                        "archived": False,
                        "limit": 20,
                        "sourceKinds": ["cli", "vscode", "exec", "appServer", "unknown"],
                        "sortKey": "updated_at",
                    },
                },
            )
            all_events.extend(_read_events_until(proc, 8, lambda events, event: event.get("id") == list_request_id))
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
    started_info = _thread_started_info(all_events, thread_id)
    listed_info = _listed_info(all_events, list_request_id or 4, thread_id)
    base_ok = bool(thread_id and _assistant_responded(all_events) and _thread_idle(all_events, thread_id) and started_info["thread_turns_empty"])
    persistence_ok = bool(started_info["thread_ephemeral"]) if ephemeral else bool(started_info["thread_persistent"] and listed_info["listed_after_start"])
    summary = {
        **plan,
        "thread_id": thread_id,
        **started_info,
        "assistant_responded": _assistant_responded(all_events),
        "thread_idle": _thread_idle(all_events, thread_id),
        **listed_info,
        **_latest_token_usage(all_events, thread_id),
        "ok": bool(base_ok and persistence_ok),
        "events": str(events_path),
        "stderr": str(stderr_path),
    }
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def run_codex_compact_thread(
    repo_root: Path,
    thread_id: str | None = None,
    handoff: Path | None = None,
    model: str | None = None,
    timeout: int = 120,
) -> dict[str, Any]:
    plan = codex_compact_thread_plan(repo_root, thread_id=thread_id, handoff=handoff, model=model)
    target_thread = plan["thread_id"]
    outdir = repo_root / ".token-economy" / "checkpoints" / "codex-app-server-compact" / datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
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
    try:
        if not target_thread:
            raise RuntimeError("No thread id supplied and CODEX_THREAD_ID is not set.")
        _send(
            proc,
            {
                "id": 1,
                "method": "initialize",
                "params": {
                    "clientInfo": {"name": "token-economy", "title": "Token Economy Compact Thread", "version": "0.1.0"},
                    "capabilities": {"experimentalApi": True},
                },
            },
        )
        all_events.extend(_read_events_until(proc, 5, lambda events, event: event.get("id") == 1))
        _send(proc, {"method": "initialized", "params": {}})
        _send(
            proc,
            {
                "id": 2,
                "method": "thread/resume",
                "params": {
                    "threadId": target_thread,
                    "cwd": str(repo_root),
                    "approvalPolicy": "never",
                    "sandbox": "workspace-write",
                    "model": plan["model"],
                    "config": {"compact_prompt": plan["compact_prompt"]},
                },
            },
        )
        all_events.extend(_read_events_until(proc, 15, lambda events, event: event.get("id") == 2 or event.get("method") == "thread/started"))
        _send(proc, {"id": 3, "method": "thread/compact/start", "params": {"threadId": target_thread}})
        all_events.extend(
            _read_events_until(
                proc,
                timeout,
                lambda events, event: bool(
                    event.get("method") == "thread/compacted"
                    and (event.get("params") or {}).get("threadId") == target_thread
                )
                or bool(event.get("method") == "error" and not event.get("willRetry")),
            )
        )
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
    resume_ok = _find_response(all_events, 2) is not None
    compact_start_ok = _find_response(all_events, 3) is not None
    compacted = any(
        event.get("method") == "thread/compacted" and (event.get("params") or {}).get("threadId") == target_thread
        for event in all_events
    )
    summary = {
        **plan,
        "thread_id": target_thread,
        "resume_ok": resume_ok,
        "compact_start_ok": compact_start_ok,
        "compacted": compacted,
        "ok": bool(resume_ok and compact_start_ok and compacted),
        "events": str(events_path),
        "stderr": str(stderr_path),
    }
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary
