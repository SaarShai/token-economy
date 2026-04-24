from __future__ import annotations

from pathlib import Path
from typing import Any

from .tokens import estimate_tokens


DEFAULT_DOC_GLOBS = ("CLAUDE.md", "AGENTS.md", "GEMINI.md", "start.md", "README.md", ".cursor/rules/*.mdc")


def audit(repo_root: Path, limit: int = 1500) -> list[dict[str, Any]]:
    rows = []
    seen = set()
    for pattern in DEFAULT_DOC_GLOBS:
        for path in repo_root.glob(pattern):
            if path in seen or not path.is_file():
                continue
            seen.add(path)
            text = path.read_text(encoding="utf-8", errors="replace")
            tokens = estimate_tokens(text)
            rows.append(
                {
                    "path": path.relative_to(repo_root).as_posix(),
                    "tokens": tokens,
                    "status": "lean" if tokens <= limit else "split",
                    "recommendation": "keep always-loaded" if tokens <= limit else "move details behind L1 pointer/wiki fetch",
                }
            )
    return rows


def split_plan(repo_root: Path, path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    headings = [line.strip("# ").strip() for line in text.splitlines() if line.startswith("#")]
    return {
        "path": path.relative_to(repo_root).as_posix() if path.is_relative_to(repo_root) else str(path),
        "tokens": estimate_tokens(text),
        "l0_keep": headings[:5],
        "l1_pointer": f"Move detailed sections into wiki pages and keep pointers in {path.name}.",
        "rule": "Always-loaded files should contain policy and pointers, not archives or examples.",
    }

