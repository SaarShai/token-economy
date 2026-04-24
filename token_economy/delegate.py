from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_MODELS = {
    "local": ["local:qwen3:8b", "local:gemma4:26b", "local:phi4:14b"],
    "cheap": ["haiku", "gpt-low"],
    "medium": ["sonnet", "gpt-medium"],
    "frontier": ["opus", "gpt-frontier"],
    "high_context": ["local:turboquant", "long-context-api"],
}


@dataclass
class Route:
    tier: str
    model_class: str
    suggested_model: str
    worker: str
    confidence: float
    parallelizable: bool
    context_policy: str
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def load_models(path: Path | None = None) -> dict[str, list[str]]:
    if not path or not path.exists():
        return DEFAULT_MODELS
    models = {k: v[:] for k, v in DEFAULT_MODELS.items()}
    current = None
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line:
            continue
        if not line.startswith(" ") and line.endswith(":"):
            current = line[:-1].strip()
            models.setdefault(current, [])
        elif current and line.strip().startswith("- "):
            models[current].append(line.strip()[2:])
    return models


def classify(task: str, registry: dict[str, list[str]] | None = None) -> Route:
    text = task.lower()
    models = registry or DEFAULT_MODELS
    high_risk = bool(re.search(r"\b(medical|legal|security|credential|delete|destructive|finance|privacy)\b", text))
    hard = bool(re.search(r"\b(architect|design|framework|multi[- ]?file|migration|novel|ambiguous|strategy|system)\b", text))
    research = bool(re.search(r"\b(research|survey|compare|find repos?|literature|web)\b", text))
    simple = bool(re.search(r"\b(typo|one[- ]?line|summari[sz]e|classify|extract|lint|format|small fix)\b", text))
    wiki = bool(re.search(r"\b(wiki|obsidian|note|memory|document|ingest)\b", text))
    parallel = bool(re.search(r"\b(parallel|independent|separate|each of|split)\b", text)) or task.count("\n- ") >= 2

    if high_risk or hard:
        return Route("hard", "frontier", models["frontier"][0], "main-orchestrator", 0.86, parallel, "retrieve exact relevant context first", "high-risk or architectural task")
    if research:
        return Route("medium", "medium", models["medium"][0], "research-worker", 0.78, parallel, "search first, fetch cited sources only", "bounded research task")
    if wiki:
        return Route("simple", "cheap", models["cheap"][0], "wiki-worker", 0.84, False, "use wiki search/timeline/fetch", "wiki/documentation task")
    if simple:
        return Route("simple", "cheap", models["cheap"][0], "quick-worker", 0.82, False, "load mentioned files only", "simple bounded task")
    if "local" in text or "ollama" in text:
        return Route("simple", "local", models["local"][0], "local-worker", 0.76, False, "local model; compact prompt", "explicit local hint")
    return Route("medium", "medium", models["medium"][0], "general-worker", 0.62, parallel, "retrieve minimally, escalate if uncertain", "default bounded task")


def delegation_plan(task: str, registry: dict[str, list[str]] | None = None) -> dict[str, Any]:
    route = classify(task, registry)
    brief = {
        "worker": route.worker,
        "model": route.suggested_model,
        "scope": "only the files/sources named or retrieved as relevant",
        "output": "compact result packet: outcome, changed files, verification, risks",
        "budget": "cheap/local for simple; medium for bounded research; frontier only for synthesis/risk",
    }
    steps = [
        "Main agent states goal and success criteria.",
        "Retrieve L1/wiki/search pointers before loading full context.",
        "Delegate independent bounded work using compact briefs." if route.parallelizable else "Handle or delegate one bounded worker task.",
        "Main agent verifies result and records durable facts after success.",
    ]
    return {"route": route.as_dict(), "brief": brief, "steps": steps}


def dumps(obj: Any) -> str:
    return json.dumps(obj, indent=2, sort_keys=True)

