from __future__ import annotations

import os
from pathlib import Path
from typing import Any


PROFILES: dict[str, dict[str, Any]] = {
    "ultra": {"startup_docs": ["start.md", "L0_rules.md", "L1_index.md"], "max_search_hits": 5, "style": "caveman-ultra"},
    "lean": {"startup_docs": ["start.md", "L0_rules.md", "L1_index.md", "index.md"], "max_search_hits": 8, "style": "terse"},
    "nav": {"startup_docs": ["start.md", "L1_index.md", "index.md", "ROADMAP.md"], "max_search_hits": 10, "style": "terse"},
    "core": {"startup_docs": ["start.md", "README.md", "index.md", "schema.md"], "max_search_hits": 12, "style": "normal-terse"},
    "full": {"startup_docs": ["start.md", "README.md", "AGENT_ONBOARDING.md", "schema.md"], "max_search_hits": 20, "style": "normal"},
}


def current_profile() -> str:
    return os.environ.get("TOKEN_ECONOMY_PROFILE", "ultra")


def profile_path(repo_root: Path) -> Path:
    return repo_root / ".token-economy-profile"


def show(repo_root: Path) -> dict[str, Any]:
    chosen = current_profile()
    path = profile_path(repo_root)
    if path.exists():
        chosen = path.read_text(encoding="utf-8").strip() or chosen
    return {"profile": chosen, "settings": PROFILES.get(chosen, PROFILES["ultra"]), "available": sorted(PROFILES)}


def set_profile(repo_root: Path, name: str) -> dict[str, Any]:
    if name not in PROFILES:
        raise KeyError(f"unknown profile: {name}")
    path = profile_path(repo_root)
    path.write_text(name + "\n", encoding="utf-8")
    return {"profile": name, "path": str(path)}

