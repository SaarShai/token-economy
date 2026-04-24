# Codex manual summ

Use this when an existing project has an older project-local Token Economy CLI. It is self-contained: it does not require `./te context codex-compact-thread` or `./te context codex-fresh-thread`.

```text
summ

Refresh context now. Do this as a context-refresh operation only.

First split this session into:
1. a lean handoff containing only what is needed to continue, and
2. durable wiki memory that should be documented but not loaded into compacted/fresh context unless needed later.

Treat any instructions after this `summ` prompt as next-session requirements. Put them in the handoff. Do not execute them in this old context.

Spawn or route a lightweight documentation worker for durable wiki memory using `prompts/subagents/wiki-documenter.prompt.md`. If that file is missing, use this inline contract: update only repo-local wiki/log after verified evidence, return changed files, summary, verification. Close the worker only after its result packet has been read and documented or folded into the handoff.

Create the handoff with `./te context checkpoint --handoff-template` or `prompts/summarize-for-handoff.md`. If the generated handoff is generic, replace it with a specific handoff from current session facts. Keep it under 2000 estimated tokens. Preserve exact paths, commands, errors, decisions, blockers, and commits. Exclude transcript noise, raw logs, broad wiki pages, and docs-only discoveries.

If available, lint it:
./te context lint-handoff <handoff-file>

If `./te context codex-compact-thread --current --handoff <handoff-file> --execute` exists, run it. Success requires `ok: true`, `resume_ok: true`, `compact_start_ok: true`, and `compacted: true`.

If that command is missing but `CODEX_THREAD_ID` exists and `codex app-server --help` works, you MUST run this self-contained App Server compaction fallback. Replace `<handoff-file>` with the actual handoff path, then execute it from the repo root:

HANDOFF="<handoff-file>" python3 - <<'PY'
import json, os, select, subprocess, time
from pathlib import Path

repo = os.getcwd()
thread_id = os.environ.get("CODEX_THREAD_ID")
handoff = os.environ["HANDOFF"]
if not os.path.isabs(handoff):
    handoff = os.path.join(repo, handoff)
model = os.environ.get("TOKEN_ECONOMY_CODEX_FRESH_MODEL") or os.environ.get("CODEX_MODEL") or "gpt-5.3-codex-spark"
compact_prompt = (
    "Compact this Codex thread for Token Economy continuation. Preserve only: current goal, repo root, "
    "files touched, commands run, errors/blockers, decisions/rationale, commits/push state, active unfinished "
    "subagents, and next actions. Exclude transcript noise, raw logs, broad wiki pages, and docs-only discoveries. "
    f"Use {handoff} as the source of truth. After compaction continue with only {repo}/start.md plus the compacted "
    "summary; retrieve more only when relevance is proven."
)
if not thread_id:
    raise SystemExit("CODEX_THREAD_ID is not set; cannot compact current thread.")

proc = subprocess.Popen(["codex", "app-server", "--listen", "stdio://"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
events = []
def send(obj):
    proc.stdin.write(json.dumps(obj) + "\n")
    proc.stdin.flush()
def read_until(timeout, pred):
    deadline = time.time() + timeout
    while time.time() < deadline:
        r, _, _ = select.select([proc.stdout], [], [], 0.2)
        if not r:
            if proc.poll() is not None:
                break
            continue
        line = proc.stdout.readline()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except Exception:
            ev = {"raw": line.rstrip("\n")}
        events.append(ev)
        if pred(ev):
            return ev
    return None

try:
    send({"id": 1, "method": "initialize", "params": {"clientInfo": {"name": "token-economy-manual-summ", "title": "Token Economy Manual Summ", "version": "0.1.0"}, "capabilities": {"experimentalApi": True}}})
    read_until(5, lambda e: e.get("id") == 1)
    send({"method": "initialized", "params": {}})
    send({"id": 2, "method": "thread/resume", "params": {"threadId": thread_id, "cwd": repo, "approvalPolicy": "never", "sandbox": "workspace-write", "model": model, "config": {"compact_prompt": compact_prompt}}})
    read_until(15, lambda e: e.get("id") == 2 or e.get("method") == "thread/started")
    send({"id": 3, "method": "thread/compact/start", "params": {"threadId": thread_id}})
    read_until(120, lambda e: (e.get("method") == "thread/compacted" and (e.get("params") or {}).get("threadId") == thread_id) or (e.get("method") == "error" and not e.get("willRetry")))
finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()

resume_ok = any(e.get("id") == 2 for e in events)
compact_start_ok = any(e.get("id") == 3 for e in events)
compacted = any(e.get("method") == "thread/compacted" and (e.get("params") or {}).get("threadId") == thread_id for e in events)
outdir = Path(".token-economy/checkpoints/manual-codex-compact")
outdir.mkdir(parents=True, exist_ok=True)
(outdir / "events.jsonl").write_text("\n".join(json.dumps(e, sort_keys=True) for e in events) + "\n", encoding="utf-8")
print(json.dumps({"ok": bool(resume_ok and compact_start_ok and compacted), "thread_id": thread_id, "resume_ok": resume_ok, "compact_start_ok": compact_start_ok, "compacted": compacted, "events": str(outdir / "events.jsonl")}, indent=2))
PY

If same-session compaction fails or `CODEX_THREAD_ID` is absent, then and only then launch a fresh successor. If `./te context codex-fresh-thread --handoff <handoff-file> --execute` is missing, use a direct App Server successor thread rather than printing a command.

Do not stop merely because local `./te` is old. The fallback script above is the older-CLI path.

After successful compact or fresh successor, continue only from `start.md` plus the handoff/compacted summary. Do not load anything else until retrieval proves relevance. Start in plan mode, think step by step, and create a robust plan before executing.
```
