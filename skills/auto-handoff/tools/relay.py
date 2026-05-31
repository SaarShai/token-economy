from __future__ import annotations

"""Auto-relay gate: decide whether a fill-threshold crossing should fire.

Logic copied + adapted from skills/handoff/tools/_lib/context.py
(`should_auto_relay` / `write_pending_relay` / `relay_state_paths`) so
auto-handoff stays self-contained. Adaptations:
- separate state dir (.token-economy/auto-handoff/state) so it can't collide
  with the legacy handoff relay state;
- carries the fill pct into the payload for the directive.

Guards against thrash:
- only fires when fill status action == "refresh";
- cooldown window (default 1800s) since the last fire;
- same-or-smaller transcript dedup (don't re-fire on the identical transcript).
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def relay_state_paths(repo_root: Path) -> dict[str, Path]:
    state_dir = repo_root / ".token-economy" / "auto-handoff" / "state"
    return {
        "dir": state_dir,
        "last": state_dir / "last-relay.json",
        "pending": state_dir / "pending-relay.json",
    }


def _now() -> float:
    return datetime.now(timezone.utc).timestamp()


def should_relay(
    repo_root: Path,
    transcript: Path | None,
    status: dict[str, Any],
    cooldown_seconds: int = 1800,
) -> dict[str, Any]:
    paths = relay_state_paths(repo_root)
    state = {k: str(v) for k, v in paths.items()}
    if status.get("action") != "refresh":
        return {"should_relay": False, "reason": "below_threshold", "state": state}
    if not transcript or not Path(transcript).exists():
        return {"should_relay": False, "reason": "transcript_unavailable", "state": state}
    stat = Path(transcript).stat()
    key = {"path": str(transcript), "size": stat.st_size}
    now = _now()
    previous: dict[str, Any] = {}
    if paths["last"].exists():
        try:
            previous = json.loads(paths["last"].read_text(encoding="utf-8"))
        except Exception:
            previous = {}
    recent = now - float(previous.get("time", 0)) < cooldown_seconds
    same_or_older = (
        previous.get("path") == key["path"] and int(previous.get("size", 0)) >= key["size"]
    )
    if recent or same_or_older:
        return {
            "should_relay": False,
            "reason": "cooldown_or_same_transcript",
            "previous": previous,
            "state": state,
        }
    payload = {
        **key,
        "time": now,
        "pct": status.get("pct"),
        "reason": "context >= refresh threshold",
    }
    return {"should_relay": True, "reason": "threshold_crossed", "payload": payload, "state": state}


def write_pending_relay(repo_root: Path, payload: dict[str, Any]) -> dict[str, str]:
    paths = relay_state_paths(repo_root)
    paths["dir"].mkdir(parents=True, exist_ok=True)
    blob = json.dumps(payload, indent=2, sort_keys=True)
    paths["last"].write_text(blob, encoding="utf-8")
    paths["pending"].write_text(blob, encoding="utf-8")
    return {k: str(v) for k, v in paths.items()}
