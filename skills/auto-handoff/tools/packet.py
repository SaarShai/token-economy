from __future__ import annotations

"""Write the lean handoff packet the successor session boots from.

Preferred path: reuse handoff's tested `checkpoint()` WITH the transcript, so the
packet carries the files/commands/errors/decisions extracted from the run (the
existing handoff.py CLI never passes a transcript, so it can't do this on its
own — we call checkpoint directly per the approved plan).

Fallback path: if skills/handoff/tools/_lib is unavailable (skill moved/removed),
write a minimal local packet from the transcript tail. This keeps auto-handoff
resilient and never hard-fails the hook.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

from meter import transcript_text
from tokens import trim_to_tokens


def _fallback_packet(goal: str, transcript_tail: str, pct: float | str) -> str:
    iso = datetime.now(timezone.utc).isoformat()
    goal = goal or "Continue the current task."
    return f"""---
type: handoff
generator: auto-handoff (fallback)
created: {iso}
context-pct-at-refresh: {pct}
next-mode: plan-first
---

# AUTO-HANDOFF (fallback packet)

## 1. Current task
{goal}

## 2. Instructions for next agent
- Start in plan mode. Build a plan before executing.
- This is a fallback packet (handoff/_lib was unavailable); it carries only the
  recent transcript tail below. Re-derive context from the repo as needed.
- Do not load anything else until retrieval proves relevance.

## 3. Recent transcript tail (model-visible content)
{transcript_tail or "- none captured"}
"""


def write_packet(
    repo_root: Path,
    transcript: Path | None,
    goal: str = "",
    pct: float | str = "unknown",
    max_tokens: int = 2000,
) -> Path:
    repo_root = Path(repo_root)
    # Preferred: reuse checkpoint() with the transcript.
    lib = repo_root / "skills" / "handoff" / "tools" / "_lib"
    if lib.is_dir():
        try:
            if str(lib) not in sys.path:
                sys.path.insert(0, str(lib))
            from context import checkpoint  # type: ignore

            result = checkpoint(
                repo_root,
                goal=goal,
                transcript=Path(transcript) if transcript else None,
                max_packet_tokens=max_tokens,
                context_pct=pct,
            )
            return Path(result["path"])
        except Exception:
            pass  # fall through to local fallback

    out_dir = repo_root / ".token-economy" / "auto-handoff"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    text = transcript_text(Path(transcript)) if transcript else ""
    tail = trim_to_tokens(text[-12000:], max_tokens)
    path = out_dir / f"{ts}-packet.md"
    path.write_text(_fallback_packet(goal, tail, pct), encoding="utf-8")
    return path
