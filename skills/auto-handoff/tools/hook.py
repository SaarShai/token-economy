#!/usr/bin/env python3
from __future__ import annotations

"""UserPromptSubmit hook: auto-checkpoint + headless successor at ~50% fill.

Every turn Claude Code passes a JSON payload on stdin (session_id,
transcript_path, cwd, prompt, ...). We estimate context fill from the transcript
and, when it crosses the refresh threshold (default 50%), write a lean packet and
spawn a detached `claude -p` successor to continue the task.

RELIABILITY CONTRACT (mirrors context-keeper): this hook MUST exit 0 on every
input. A non-zero UserPromptSubmit hook can block the user's prompt. All work is
wrapped so any error degrades to a silent exit 0.
"""

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))


def _truthy(value: str | None) -> bool:
    return value not in (None, "", "0", "false", "False", "no")


def _infer_goal(transcript: Path | None) -> str:
    """Best-effort: the most recent user message, for the packet title/summary."""
    if not transcript or not transcript.exists():
        return ""
    last = ""
    for line in transcript.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if not isinstance(obj, dict) or obj.get("type") != "user":
            continue
        content = (obj.get("message") or {}).get("content")
        if isinstance(content, str):
            last = content
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and isinstance(block.get("text"), str):
                    last = block["text"]
    return last.strip().replace("\n", " ")[:120]


def _emit_directive(pct, packet: Path, record: dict) -> None:
    status = record.get("status")
    lines = ["<system-reminder>", f"AUTO-HANDOFF — context at {pct}% (>= refresh threshold)."]
    if status == "notified":
        # detection-only (default): nothing spawned; hand the user a launch command.
        lines += [
            "A lean handoff packet was written. NO successor was spawned (detection-only mode).",
            f"- packet: {packet}",
            "To continue in fresh context, the user opens a NEW interactive session in this repo",
            "(subscription auth) and runs:",
            f"    {record.get('cmd_str')}",
            "ACTION: tell the user context is high, point them at the packet, and give them the",
            "command above. Then wind down new work here.",
        ]
    elif status == "dryrun":
        lines += [
            "Headless successor spawn PLANNED (dry-run, not launched):",
            f"- packet: {packet}",
            f"- command: {record.get('cmd_str')}",
            "Surface the packet path + command to the user.",
        ]
    else:  # launched
        lines += [
            "Headless successor SPAWNED to continue this task:",
            f"- packet: {packet}",
            f"- pid: {record.get('pid')}   log: {record.get('log')}",
            f"- command: {record.get('cmd_str')}",
            "- successor carries AUTO_HANDOFF_DISABLE=1, so it will NOT spawn further sessions.",
            "STAND DOWN: the successor owns continuation; give the user the pid + log path.",
        ]
    lines.append("</system-reminder>")
    sys.stdout.write("\n".join(lines) + "\n")


CONFIG_ENV_MAP = {
    "mode": "AUTO_HANDOFF_MODE",
    "refresh_at_pct": "REFRESH_AT_PCT",
    "warn_at_pct": "WARN_AT_PCT",
    "cooldown": "AUTO_HANDOFF_COOLDOWN",
    "budget_usd": "AUTO_HANDOFF_BUDGET_USD",
    "gen_cap": "AUTO_HANDOFF_GEN_CAP",
    "context_max": "TOKEN_ECONOMY_CONTEXT_MAX",
    "disable": "AUTO_HANDOFF_DISABLE",
    "dryrun": "AUTO_HANDOFF_DRYRUN",
}


def _apply_config_defaults(repo_root: Path) -> dict:
    """Populate env defaults from .token-economy/auto-handoff/config.json.

    Uses setdefault so a real environment variable always wins. This is the
    only knob that works mid-session: Claude Code's process env can't be changed
    once it's running, but hook.py re-reads this file fresh every turn.
    """
    cfg_path = repo_root / ".token-economy" / "auto-handoff" / "config.json"
    if not cfg_path.exists():
        return {}
    try:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(cfg, dict):
        return {}
    for key, env_name in CONFIG_ENV_MAP.items():
        if cfg.get(key) is not None:
            os.environ.setdefault(env_name, str(cfg[key]))
    return cfg


def main() -> int:
    raw = ""
    try:
        if not sys.stdin.isatty():
            raw = sys.stdin.read()
    except Exception:
        raw = ""
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        payload = {}

    cwd = payload.get("cwd") or os.getcwd()
    repo_root = Path(cwd)
    transcript_path = payload.get("transcript_path", "")
    transcript = Path(transcript_path) if transcript_path else None

    # Disk config populates env defaults (real env still wins). Lets you tune
    # threshold/cooldown/disable mid-session without restarting Claude Code.
    _apply_config_defaults(repo_root)

    # anti-fork-bomb: successors run with AUTO_HANDOFF_DISABLE=1.
    if _truthy(os.environ.get("AUTO_HANDOFF_DISABLE")):
        return 0

    # 1) generation cap (backstop; DISABLE already covers the normal successor case).
    try:
        gen = int(os.environ.get("AUTO_HANDOFF_GEN", "0") or 0)
        cap = int(os.environ.get("AUTO_HANDOFF_GEN_CAP", "3") or 3)
    except ValueError:
        gen, cap = 0, 3
    if gen >= cap:
        return 0

    from meter import fill_status
    from relay import should_relay, write_pending_relay

    status = fill_status(transcript)
    try:
        cooldown = int(os.environ.get("AUTO_HANDOFF_COOLDOWN", "1800") or 1800)
    except ValueError:
        cooldown = 1800
    gate = should_relay(repo_root, transcript, status, cooldown_seconds=cooldown)
    if not gate.get("should_relay"):
        return 0

    # FIRE. Record state first (starts the cooldown), then packet + spawn.
    write_pending_relay(repo_root, gate["payload"])

    from packet import write_packet
    from spawn import launch, notify

    packet = write_packet(
        repo_root, transcript, goal=_infer_goal(transcript), pct=status.get("pct", "unknown")
    )
    # Default mode is detection-only ("notify"): write packet + hand the user an
    # interactive launch command. "spawn" opts into headless `claude -p` (needs
    # an API key; 401s on OAuth-only auth).
    mode = (os.environ.get("AUTO_HANDOFF_MODE") or "notify").strip().lower()
    record = launch(repo_root, packet, gen=gen) if mode == "spawn" else notify(repo_root, packet, gen=gen)
    _emit_directive(status.get("pct"), packet, record)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # never block the prompt
        sys.stderr.write(f"[auto-handoff] non-fatal: {exc}\n")
        sys.exit(0)
