"""Progressive-disclosure wiki retrieval API.

Small importable wrapper around `token_economy.wiki.WikiStore`.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from token_economy.config import load_config
from token_economy.wiki import WikiStore


def _store(root: str | None = None) -> WikiStore:
    cfg = load_config(REPO_ROOT)
    return WikiStore(root or cfg.wiki_root)


def wiki_search(query: str, k: int = 10, root: str | None = None) -> list[dict[str, Any]]:
    return _store(root).search(query, k)


def wiki_timeline(item_id: str, window: int = 3, root: str | None = None) -> dict[str, Any]:
    return _store(root).timeline(item_id, window)


def wiki_fetch(item_id: str, root: str | None = None) -> dict[str, Any]:
    return _store(root).fetch(item_id)

