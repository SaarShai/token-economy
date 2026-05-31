#!/usr/bin/env python3
"""Integration tests for the auto-handoff gate + packet + spawn (all dry-run).

Run: python3 skills/auto-handoff/tools/test_hook.py
NEVER launches a real `claude` (AUTO_HANDOFF_DRYRUN=1 forced everywhere).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
HOOK = HERE / "hook.py"
sys.path.insert(0, str(HERE))

from packet import write_packet  # noqa: E402


def _transcript(path: Path, n_lines: int, text_per_line: str) -> None:
    with path.open("w", encoding="utf-8") as f:
        for _ in range(n_lines):
            f.write(
                json.dumps(
                    {
                        "type": "assistant",
                        "message": {"role": "assistant", "content": [{"type": "text", "text": text_per_line}]},
                    }
                )
                + "\n"
            )
        # one user line so _infer_goal has something
        f.write(
            json.dumps({"type": "user", "message": {"role": "user", "content": "fix the meter at skills/auto-handoff/tools/meter.py"}})
            + "\n"
        )


def _run_hook(payload: dict, env_extra: dict, cwd: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["TOKEN_ECONOMY_CONTEXT_MAX"] = "10000"
    env["AUTO_HANDOFF_DRYRUN"] = "1"  # never launch a real claude
    for k in ("AUTO_HANDOFF_DISABLE", "AUTO_HANDOFF_GEN", "AUTO_HANDOFF_GEN_CAP", "REFRESH_AT_PCT", "AUTO_HANDOFF_COOLDOWN"):
        env.pop(k, None)
    env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        cwd=str(cwd),
    )


def _clean_state(repo: Path) -> None:
    shutil.rmtree(repo / ".token-economy", ignore_errors=True)


def main() -> int:
    results = []

    # ===== Packet: reuse path (real repo has skills/handoff/tools/_lib) =====
    tmp = Path(tempfile.mkdtemp(prefix="autohandoff-it-"))
    t = tmp / "transcript.jsonl"
    _transcript(t, 55, "x" * 400)
    p_reuse = write_packet(REPO_ROOT, t, goal="meter fix", pct=55.0)
    reuse_text = p_reuse.read_text(encoding="utf-8")
    assert p_reuse.exists(), p_reuse
    assert "Start in plan mode" in reuse_text, "reuse packet missing plan-mode instruction"
    assert "fresh-session" in p_reuse.name, ("expected checkpoint() reuse path", p_reuse)
    results.append(("packet.reuse", f"{p_reuse.name} ({len(reuse_text)}b)"))

    # ===== Packet: fallback path (temp repo, no handoff lib) =====
    p_fb = write_packet(tmp, t, goal="meter fix", pct=55.0)
    fb_text = p_fb.read_text(encoding="utf-8")
    assert "fallback packet" in fb_text and "Start in plan mode" in fb_text, fb_text[:200]
    assert (tmp / ".token-economy" / "auto-handoff") in p_fb.parents, p_fb
    results.append(("packet.fallback", p_fb.name))

    # ===== Hook gate cases (subprocess, dry-run) =====
    payload = {"transcript_path": str(t), "cwd": str(tmp), "session_id": "test"}

    # Case A: 55% + clean state -> FIRE (default mode=notify, detection-only)
    _clean_state(tmp)
    _transcript(t, 55, "x" * 400)
    a = _run_hook(payload, {}, tmp)
    assert a.returncode == 0, a
    assert "AUTO-HANDOFF" in a.stdout and "detection-only" in a.stdout, ("expected notify fire", a.stdout, a.stderr)
    manifest = json.loads((tmp / ".token-economy" / "auto-handoff" / "manifest.json").read_text())
    assert manifest[-1]["status"] == "notified", manifest[-1]
    cs = manifest[-1]["cmd_str"]
    assert cs.startswith("claude --add-dir") and "-p" not in cs.split() and "--max-budget-usd" not in cs, manifest[-1]
    assert (tmp / ".token-economy" / "auto-handoff" / "state" / "pending-relay.json").exists()
    results.append(("gate.fire@55% notify", f"status=notified; cmd={cs[:50]}..."))

    # Case A2: mode=spawn -> headless command PLANNED (dry-run forced in test env), not launched
    _clean_state(tmp)
    _transcript(t, 55, "x" * 400)
    a2 = _run_hook(payload, {"AUTO_HANDOFF_MODE": "spawn"}, tmp)
    assert a2.returncode == 0 and "AUTO-HANDOFF" in a2.stdout, a2.stdout
    m2 = json.loads((tmp / ".token-economy" / "auto-handoff" / "manifest.json").read_text())
    assert m2[-1]["status"] == "dryrun", m2[-1]
    assert "claude -p" in m2[-1]["cmd_str"] and "--max-budget-usd" in m2[-1]["cmd_str"], m2[-1]
    results.append(("gate.fire@55% spawn/dry", f"cmd={m2[-1]['cmd_str'][:50]}..."))

    # Case B: immediately again -> COOLDOWN, no fire (state preserved)
    b = _run_hook(payload, {}, tmp)
    assert b.returncode == 0 and "AUTO-HANDOFF" not in b.stdout, ("expected cooldown", b.stdout)
    results.append(("gate.cooldown", "no re-fire (recent last-relay)"))

    # Case C: clean state but AUTO_HANDOFF_DISABLE=1 -> no fire (anti-fork-bomb)
    _clean_state(tmp)
    c = _run_hook(payload, {"AUTO_HANDOFF_DISABLE": "1"}, tmp)
    assert c.returncode == 0 and "AUTO-HANDOFF" not in c.stdout, ("disable should suppress", c.stdout)
    assert not (tmp / ".token-economy").exists(), "disabled hook must not write state"
    results.append(("loop-safety.disable", "successor env suppresses fire + writes nothing"))

    # Case D: clean state but AUTO_HANDOFF_GEN at cap -> no fire
    _clean_state(tmp)
    d = _run_hook(payload, {"AUTO_HANDOFF_GEN": "3", "AUTO_HANDOFF_GEN_CAP": "3"}, tmp)
    assert d.returncode == 0 and "AUTO-HANDOFF" not in d.stdout, ("gen-cap should suppress", d.stdout)
    results.append(("loop-safety.gen-cap", "gen>=cap suppresses fire"))

    # Case E: 20% fill -> below threshold, no fire
    _clean_state(tmp)
    _transcript(t, 20, "x" * 400)
    e = _run_hook(payload, {}, tmp)
    assert e.returncode == 0 and "AUTO-HANDOFF" not in e.stdout, ("below-threshold should not fire", e.stdout)
    results.append(("gate.below@20%", "no fire"))

    print("auto-handoff integration: all cases pass\n")
    for name, detail in results:
        print(f"  PASS  {name:24}  {detail}")
    print("\nOK 8/8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
