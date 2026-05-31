from __future__ import annotations

from math import ceil


def estimate_tokens(text: str) -> int:
    """Cheap model-agnostic token estimate.

    Conservative char/4 heuristic plus newline overhead. Good enough for
    threshold triggers where exact provider tokenization is unavailable.

    Copied verbatim from skills/handoff/tools/_lib/tokens.py — auto-handoff is
    self-contained by design (the repo already duplicates this estimator across
    skills) so removing or moving `handoff` can never break it.
    """
    if not text:
        return 0
    return max(1, ceil(len(text) / 4) + text.count("\n"))


def trim_to_tokens(text: str, limit: int) -> str:
    if estimate_tokens(text) <= limit:
        return text
    lines = text.splitlines()
    kept: list[str] = []
    for line in lines:
        candidate = "\n".join([*kept, line, "...[trimmed]..."])
        if estimate_tokens(candidate) > limit:
            break
        kept.append(line)
    return "\n".join([*kept, "...[trimmed]..."]) + "\n"
