from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .codex_app import run_ask_old, run_fresh_thread
from .core import ask_old_plan, checkpoint, current_codex_transcript, lint_handoff, relay_session_name


def print_json(obj: Any) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="relay-session")
    parser.add_argument("--repo", default=".")
    sub = parser.add_subparsers(dest="cmd", required=True)

    cp = sub.add_parser("checkpoint")
    cp.add_argument("--goal", default="Continue current work")
    cp.add_argument("--plan", default="")
    cp.add_argument("--transcript")
    cp.add_argument("--max-tokens", type=int, default=2000)

    lint = sub.add_parser("lint")
    lint.add_argument("--handoff", required=True)
    lint.add_argument("--max-tokens", type=int, default=2000)

    launch = sub.add_parser("launch")
    launch.add_argument("--handoff", required=True)
    launch.add_argument("--name", default=None)
    launch.add_argument("--version", default="01")
    launch.add_argument("--model", default=None)
    launch.add_argument("--execute", action="store_true")
    launch.add_argument("--timeout", type=int, default=120)
    launch.add_argument("--stop-after-verify", action="store_true")

    relay = sub.add_parser("relay")
    relay.add_argument("--goal", default=None)
    relay.add_argument("--plan", default="Fresh successor should continue from this handoff.")
    relay.add_argument("--name", default="auto-context-refresh")
    relay.add_argument("--version", default="01")
    relay.add_argument("--model", default=None)
    relay.add_argument("--execute", action="store_true")
    relay.add_argument("--timeout", type=int, default=120)

    ask = sub.add_parser("ask-old")
    ask.add_argument("--handoff", required=True)
    ask.add_argument("--question", required=True)
    ask.add_argument("--model", default=None)
    ask.add_argument("--execute", action="store_true")
    ask.add_argument("--timeout", type=int, default=120)

    args = parser.parse_args(argv)
    repo = Path(args.repo).expanduser().resolve()

    if args.cmd == "checkpoint":
        transcript = Path(args.transcript).expanduser() if args.transcript else current_codex_transcript()
        print_json(checkpoint(repo, args.goal, plan=args.plan, transcript=transcript, max_packet_tokens=args.max_tokens))
        return 0
    if args.cmd == "lint":
        handoff = Path(args.handoff).expanduser()
        if not handoff.is_absolute():
            handoff = repo / handoff
        result = lint_handoff(handoff, max_tokens=args.max_tokens)
        print_json(result)
        return 0 if result["ok"] else 1
    if args.cmd == "launch":
        handoff = Path(args.handoff).expanduser()
        if not handoff.is_absolute():
            handoff = repo / handoff
        session_name = relay_session_name(args.name, args.version) if args.name else None
        if not args.execute:
            print_json({"ok": True, "execute": False, "session_name": session_name, "handoff": str(handoff)})
            return 0
        print_json(run_fresh_thread(repo, handoff, session_name=session_name, model=args.model, timeout=args.timeout, continue_work=not args.stop_after_verify))
        return 0
    if args.cmd == "relay":
        session_name = relay_session_name(args.name, args.version)
        transcript = current_codex_transcript()
        packet = checkpoint(repo, args.goal or f"Automatic relay for {session_name}", plan=args.plan, transcript=transcript)
        handoff = Path(packet["path"])
        result: dict[str, Any] = {"ok": True, "session_name": session_name, "handoff": str(handoff), "handoff_tokens": packet["tokens"], "execute": args.execute}
        if args.execute:
            result["successor"] = run_fresh_thread(repo, handoff, session_name=session_name, model=args.model, timeout=args.timeout, continue_work=True)
            result["ok"] = bool(result["successor"].get("ok"))
        print_json(result)
        return 0 if result["ok"] else 1
    if args.cmd == "ask-old":
        handoff = Path(args.handoff).expanduser()
        if not handoff.is_absolute():
            handoff = repo / handoff
        plan = ask_old_plan(repo, handoff, args.question, execute=args.execute)
        if args.execute and plan.get("mode") == "codex-old-thread":
            print_json(run_ask_old(repo, str(plan["thread_id"]), args.question, model=args.model, timeout=args.timeout))
        else:
            print_json(plan)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

