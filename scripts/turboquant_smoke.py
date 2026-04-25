#!/usr/bin/env python3
"""Smoke checks for the local TurboQuant llama-server path.

Default mode is non-invasive: inspect wrapper/server artifacts and health if the
server is already running. Use --require-server when a live server is expected.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


REQUIRED_HELP_TERMS = ("cache-type-k", "cache-type-v", "turbo4")


def has_cache_flags(help_text: str) -> bool:
    lowered = help_text.lower()
    return all(term in lowered for term in REQUIRED_HELP_TERMS)


def run_cmd(cmd: list[str], timeout: int = 5) -> tuple[int | None, str]:
    try:
        proc = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
    except FileNotFoundError:
        return None, "not found"
    except subprocess.TimeoutExpired:
        return None, "timeout"
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def health(url: str, timeout: int = 2) -> tuple[bool, str]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read(200).decode("utf-8", errors="replace")
            return response.status < 500, body
    except urllib.error.HTTPError as exc:
        return exc.code < 500, str(exc)
    except Exception as exc:
        return False, str(exc)


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    wrapper = Path(args.wrapper).expanduser()
    server_bin = Path(args.server_bin).expanduser()
    report: dict[str, Any] = {
        "wrapper": str(wrapper),
        "wrapper_exists": wrapper.exists(),
        "server_bin": str(server_bin),
        "server_bin_exists": server_bin.exists(),
        "required_help_terms": list(REQUIRED_HELP_TERMS),
    }

    if args.help_text_file:
        help_text = Path(args.help_text_file).read_text(encoding="utf-8", errors="replace")
        report["help_source"] = str(Path(args.help_text_file))
        report["cache_flags_supported"] = has_cache_flags(help_text)
    elif server_bin.exists():
        code, output = run_cmd([str(server_bin), "--help"], timeout=args.timeout)
        report["help_exit_code"] = code
        report["cache_flags_supported"] = has_cache_flags(output)
    else:
        report["cache_flags_supported"] = False

    if wrapper.exists():
        code, output = run_cmd([str(wrapper), "status"], timeout=args.timeout)
        report["wrapper_status_exit_code"] = code
        report["wrapper_status"] = output[:500]

    ok, detail = health(f"http://{args.host}:{args.port}/health", timeout=args.timeout)
    report["server_health_ok"] = ok
    report["server_health_detail"] = detail[:500]
    report["safe_q4km_default"] = "-ctk q8_0 -ctv turbo4"
    report["require_server"] = args.require_server
    report["ok"] = bool(report["cache_flags_supported"]) and (ok or not args.require_server)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check local TurboQuant llama-server readiness")
    parser.add_argument("--wrapper", default="~/bin/llama-tq")
    parser.add_argument("--server-bin", default="~/src/llama-cpp-turboquant/build/bin/llama-server")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--timeout", type=int, default=5)
    parser.add_argument("--require-server", action="store_true")
    parser.add_argument("--help-text-file", help="Test/parser mode: read llama-server --help text from a file")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    report = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for key, value in report.items():
            print(f"{key}: {value}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
