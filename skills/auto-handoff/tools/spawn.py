from __future__ import annotations

"""Spawn the headless successor session that continues the task.

Builds a `claude -p` command pointed at the lean packet and launches it
detached (its own session, survives this turn). Safety rails baked in:

- `--max-budget-usd` caps the successor's spend (default $2; AUTO_HANDOFF_BUDGET_USD).
- child env `AUTO_HANDOFF_DISABLE=1` -> the successor's own hook no-ops, so it
  can never spawn a grandchild (anti-fork-bomb).
- child env `AUTO_HANDOFF_GEN=<n+1>` -> generation depth, a second backstop.
- `start_new_session=True` + stdin=DEVNULL -> fully detached from the hook.
- stdout/stderr -> .token-economy/auto-handoff/successor-<ts>.log; every launch
  appended to manifest.json for visibility.
- AUTO_HANDOFF_DRYRUN truthy -> build + record the command but DON'T launch.
"""

import json
import os
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_BUDGET_USD = "2"


def _truthy(value: str | None) -> bool:
    return value not in (None, "", "0", "false", "False", "no")


def successor_prompt(packet: Path) -> str:
    return (
        f"Read {packet} only. Continue from that handoff. Start in plan mode. "
        "Do not load anything else until retrieval proves relevance."
    )


def build_command(repo_root: Path, packet: Path, budget_usd: str | None = None) -> list[str]:
    budget = budget_usd or os.environ.get("AUTO_HANDOFF_BUDGET_USD", DEFAULT_BUDGET_USD)
    return [
        "claude",
        "-p",
        "--add-dir",
        str(repo_root),
        "--max-budget-usd",
        str(budget),
        successor_prompt(packet),
    ]


def child_env(gen: int) -> dict[str, str]:
    env = dict(os.environ)
    env["AUTO_HANDOFF_DISABLE"] = "1"  # successor's hook no-ops -> no grandchildren
    env["AUTO_HANDOFF_GEN"] = str(gen + 1)
    return env


def _append_manifest(log_dir: Path, record: dict[str, Any]) -> None:
    manifest = log_dir / "manifest.json"
    data: list[Any] = []
    if manifest.exists():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                data = []
        except Exception:
            data = []
    data.append(record)
    manifest.write_text(json.dumps(data, indent=2), encoding="utf-8")


def launch(
    repo_root: Path,
    packet: Path,
    gen: int = 0,
    dryrun: bool | None = None,
) -> dict[str, Any]:
    repo_root = Path(repo_root)
    packet = Path(packet)
    log_dir = repo_root / ".token-economy" / "auto-handoff"
    log_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    cmd = build_command(repo_root, packet)
    if dryrun is None:
        dryrun = _truthy(os.environ.get("AUTO_HANDOFF_DRYRUN"))

    record: dict[str, Any] = {
        "ts": ts,
        "packet": str(packet),
        "gen": gen,
        "child_gen": gen + 1,
        "disable_in_child": True,
        "cmd": cmd,
        "cmd_str": " ".join(shlex.quote(c) for c in cmd),
    }

    if dryrun:
        record["status"] = "dryrun"
        _append_manifest(log_dir, record)
        return record

    log_path = log_dir / f"successor-{ts}.log"
    with log_path.open("w", encoding="utf-8") as fh:
        proc = subprocess.Popen(
            cmd,
            cwd=str(repo_root),
            env=child_env(gen),
            stdout=fh,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    record.update({"status": "launched", "pid": proc.pid, "log": str(log_path)})
    _append_manifest(log_dir, record)
    return record


def interactive_command(repo_root: Path, packet: Path) -> list[str]:
    """Interactive successor command (no `-p`) — runs on the logged-in
    subscription session, so no API key and no per-call metering. This is the
    default: the user launches it in a fresh window."""
    return ["claude", "--add-dir", str(repo_root), successor_prompt(packet)]


def notify(repo_root: Path, packet: Path, gen: int = 0) -> dict[str, Any]:
    """Detection-only: record the ready-to-run launch command, spawn nothing.

    The headless `claude -p` path needs an API key (metered) and 401s on
    OAuth-only auth; notify hands the command to the user to run in a fresh
    interactive (subscription) session instead.
    """
    repo_root = Path(repo_root)
    packet = Path(packet)
    log_dir = repo_root / ".token-economy" / "auto-handoff"
    log_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    cmd = interactive_command(repo_root, packet)
    record = {
        "ts": ts,
        "packet": str(packet),
        "gen": gen,
        "status": "notified",
        "mode": "notify",
        "cmd": cmd,
        "cmd_str": " ".join(shlex.quote(c) for c in cmd),
    }
    _append_manifest(log_dir, record)
    return record


def _main() -> int:
    import argparse

    p = argparse.ArgumentParser(prog="spawn", description="Spawn / dry-run the auto-handoff successor.")
    p.add_argument("--repo", default=".")
    p.add_argument("--packet", required=True)
    p.add_argument("--gen", type=int, default=0)
    p.add_argument("--dryrun", action="store_true", help="force dry-run regardless of env")
    args = p.parse_args()
    rec = launch(Path(args.repo), Path(args.packet), gen=args.gen, dryrun=True if args.dryrun else None)
    json.dump(rec, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
