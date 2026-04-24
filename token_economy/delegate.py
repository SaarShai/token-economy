from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_MODELS = {
    "reasoning_top": ["opus", "gpt-frontier", "gemini-pro", "local:deepseek-r1:32b"],
    "coding_top": ["sonnet", "gpt-coding", "gemini-pro", "local:qwen-coder"],
    "medium": ["sonnet", "gpt-medium"],
    "lightweight": ["haiku", "gpt-low", "gemini-flash", "local:qwen3:8b"],
    "local": ["local:qwen3:8b", "local:gemma4:26b", "local:phi4:14b"],
    "high_context": ["local:turboquant", "long-context-api"],
}

EFFORT_GUIDANCE = {
    "reasoning_top": {"anthropic": "thinking: high", "openai": "reasoning.effort: high", "google": "thinking_budget: high", "local": "allow reasoning, concise final"},
    "coding_top": {"anthropic": "thinking: medium", "openai": "reasoning.effort: medium", "google": "thinking_budget: medium", "local": "code-focused prompt"},
    "medium": {"anthropic": "thinking: low/medium", "openai": "reasoning.effort: medium", "google": "thinking_budget: medium", "local": "bounded exploration"},
    "lightweight": {"anthropic": "thinking: low", "openai": "reasoning.effort: low", "google": "thinking_budget: low", "local": "concise; skip exploration"},
    "local": {"anthropic": "n/a", "openai": "n/a", "google": "n/a", "local": "single compact prompt"},
    "high_context": {"anthropic": "cache/retrieve first", "openai": "low effort unless synthesis", "google": "budget by task", "local": "TurboQuant/long-context server"},
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
    if "cheap" in models and "lightweight" not in models:
        models["lightweight"] = models["cheap"]
    if "frontier" in models and "reasoning_top" not in models:
        models["reasoning_top"] = models["frontier"]
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
        return Route("hard", "reasoning_top", models["reasoning_top"][0], "main-orchestrator", 0.86, parallel, "retrieve exact relevant context first", "high-risk or architectural task")
    if research:
        return Route("medium", "medium", models["medium"][0], "research-worker", 0.78, parallel, "search first, fetch cited sources only", "bounded research task")
    if wiki:
        return Route("simple", "lightweight", models["lightweight"][0], "wiki-worker", 0.84, False, "use wiki search/timeline/fetch", "wiki/documentation task")
    if simple:
        return Route("simple", "lightweight", models["lightweight"][0], "quick-worker", 0.82, False, "load mentioned files only", "simple bounded task")
    if "local" in text or "ollama" in text:
        return Route("simple", "local", models["local"][0], "local-worker", 0.76, False, "local model; compact prompt", "explicit local hint")
    return Route("medium", "medium", models["medium"][0], "general-worker", 0.62, parallel, "retrieve minimally, escalate if uncertain", "default bounded task")


def delegation_plan(task: str, registry: dict[str, list[str]] | None = None) -> dict[str, Any]:
    route = classify(task, registry)
    rejected = [tier for tier in ("reasoning_top", "coding_top", "medium", "lightweight", "local", "high_context") if tier != route.model_class]
    brief = {
        "worker": route.worker,
        "model": route.suggested_model,
        "scope": "only the files/sources named or retrieved as relevant",
        "output": "compact result packet: outcome, changed files, verification, sources, confidence, risks",
        "budget": "lightweight/local for simple; medium for bounded research; reasoning_top only for synthesis/risk",
    }
    steps = [
        "Main agent states goal and success criteria.",
        "Retrieve L1/wiki/search pointers before loading full context.",
        "Delegate independent bounded work using compact briefs." if route.parallelizable else "Handle or delegate one bounded worker task.",
        "Reject subagent reports missing sources/confidence.",
        "Orchestrator keeps final synthesis and final plan authorship.",
        "Main agent verifies result and records durable facts after success.",
    ]
    return {
        "task_class": route.tier,
        "route": route.as_dict(),
        "chosen_tier": route.model_class,
        "rejected_tiers": rejected,
        "effort": EFFORT_GUIDANCE.get(route.model_class, {}),
        "minimal_context_bundle": ["task", "success criteria", "only relevant paths/sources", "budget", "expected output"],
        "result_contract": ["outcome", "sources", "confidence", "verification", "changed files", "risks"],
        "orchestrator_rule": "Orchestrator does not delegate final synthesis.",
        "brief": brief,
        "steps": steps,
    }


def dumps(obj: Any) -> str:
    return json.dumps(obj, indent=2, sort_keys=True)
