from __future__ import annotations

from pathlib import Path
from typing import Any


HOOKS = [
    "hooks/context-check.sh",
    "hooks/pre-compact.sh",
    "hooks/session-start.sh",
    "hooks/user-prompt-submit.sh",
    "hooks/output-filter/filter.sh",
]


def doctor(repo_root: Path) -> dict[str, Any]:
    rows = []
    ok = True
    for rel in HOOKS:
        path = repo_root / rel
        exists = path.exists()
        executable = path.exists() and bool(path.stat().st_mode & 0o111)
        rows.append({"path": rel, "exists": exists, "executable": executable})
        ok = ok and exists and executable
    return {"ok": ok, "hooks": rows}

