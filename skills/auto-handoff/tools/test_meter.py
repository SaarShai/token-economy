#!/usr/bin/env python3
"""Unit tests for the auto-handoff fill meter.

Run: python3 skills/auto-handoff/tools/test_meter.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from meter import fill_status, resolve_max_tokens, transcript_text  # noqa: E402


def _write_transcript(path: Path, n_lines: int, text_per_line: str) -> None:
    with path.open("w", encoding="utf-8") as f:
        for _ in range(n_lines):
            f.write(
                json.dumps(
                    {
                        "type": "assistant",
                        "uuid": "00000000-0000-0000-0000-000000000000",
                        "message": {
                            "role": "assistant",
                            "content": [{"type": "text", "text": text_per_line}],
                        },
                    }
                )
                + "\n"
            )


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="autohandoff-meter-"))
    t = tmp / "transcript.jsonl"
    line_text = "x" * 400  # ~100 tokens of visible content per line

    # Deterministic max so ratios are exact regardless of model defaults.
    os.environ["TOKEN_ECONOMY_CONTEXT_MAX"] = "10000"
    os.environ.pop("REFRESH_AT_PCT", None)
    os.environ.pop("WARN_AT_PCT", None)
    assert resolve_max_tokens() == 10000

    # --- Case A: ~55% full -> action "refresh" ---
    _write_transcript(t, 55, line_text)
    a = fill_status(t)
    assert a["max_tokens"] == 10000, a
    assert 50 <= a["pct"] <= 62, ("pct out of band", a)
    assert a["action"] == "refresh", ("expected refresh", a)

    # content extraction must strip JSON scaffolding: content estimate < raw-bytes estimate
    from tokens import estimate_tokens

    content_est = a["estimated_tokens"]
    raw_est = estimate_tokens(t.read_text(encoding="utf-8"))
    assert content_est < raw_est, ("content should be < raw bytes", content_est, raw_est)

    # --- Case B: ~20% full -> action "continue" ---
    _write_transcript(t, 20, line_text)
    b = fill_status(t)
    assert 15 <= b["pct"] <= 25, ("pct out of band", b)
    assert b["action"] == "continue", ("expected continue", b)

    # --- Case C: env override REFRESH_AT_PCT=18 (percent form) lowers the bar ---
    os.environ["REFRESH_AT_PCT"] = "18"
    c = fill_status(t)
    assert c["refresh_threshold"] == 0.18, c
    assert c["action"] == "refresh", ("expected refresh after lowering bar", c)
    os.environ.pop("REFRESH_AT_PCT", None)

    # --- Case D: missing / empty transcript -> 0%, continue (never crashes) ---
    d = fill_status(tmp / "does-not-exist.jsonl")
    assert d["estimated_tokens"] == 0 and d["action"] == "continue", d
    assert transcript_text(None) == ""

    print("A(55):", json.dumps(a))
    print("B(20):", json.dumps(b))
    print("C(override):", json.dumps(c))
    print("D(empty):", json.dumps(d))
    print(f"content_est={content_est} < raw_est={raw_est}  (scaffolding stripped)")
    print("OK meter: 4/4 cases pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
