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
from token_economy.code_map import code_map as build_code_map
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


def wiki_context(task: str, max_pages: int = 5, max_tokens: int = 4000, root: str | None = None) -> dict[str, Any]:
    return _store(root).context(task, max_pages=max_pages, max_tokens=max_tokens)


def code_map(query: str = "", max_files: int = 20, max_symbols: int = 200, root: str | None = None) -> dict[str, Any]:
    cfg = load_config(REPO_ROOT)
    return build_code_map(root or cfg.repo_root, query=query, max_files=max_files, max_symbols=max_symbols)
