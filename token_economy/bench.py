from __future__ import annotations

from pathlib import Path
from typing import Any

from .code_map import code_map
from .context import checkpoint, meter
from .delegate import classify
from .tokens import estimate_tokens
from .wiki import WikiStore


def run_framework_smoke(repo_root: Path) -> dict[str, Any]:
    wiki = WikiStore(repo_root)
    hits = wiki.search("context refresh", 3)
    code = code_map(repo_root, query="WikiStore context", max_files=3, max_symbols=30)
    route = classify("summarize this wiki note and document the result")
    packet = checkpoint(repo_root, goal="framework smoke benchmark", plan="verify core paths")
    sample = "Find context refresh docs, classify delegation, create handoff."
    tasks = [
        {"name": "wiki_query", "ok": isinstance(hits, list), "tokens": estimate_tokens(str(hits))},
        {"name": "code_map", "ok": code["returned_files"] >= 1, "tokens": code["token_estimate"]},
        {"name": "context_refresh", "ok": packet["tokens"] <= 2000, "tokens": packet["tokens"]},
        {"name": "delegation_classification", "ok": route.model_class != "reasoning_top", "tokens": estimate_tokens(str(route.as_dict()))},
        {"name": "code_extraction", "ok": (repo_root / "token_economy/wiki.py").exists(), "tokens": estimate_tokens(sample)},
        {"name": "research_summary", "ok": (repo_root / "prompts/subagents/research-lite.prompt.md").exists(), "tokens": estimate_tokens(sample)},
    ]
    return {
        "suite": "framework-smoke",
        "tasks": tasks,
        "ok": all(t["ok"] for t in tasks),
        "total_estimated_tokens": sum(t["tokens"] for t in tasks),
        "quality_rubric": "smoke only: validates interfaces; does not claim savings",
    }
