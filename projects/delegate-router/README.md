---
type: project
axis: skill_crystallization
tags: [delegation, routing, subagents, models]
confidence: med
evidence_count: 1
---

# delegate-router

Model-agnostic routing policy for subagents and cheaper models.

## Contract

- Prefer cheapest capable worker.
- Use local/cheap models for extraction, summaries, lint, simple edits, wiki updates, and classification.
- Use medium models for bounded research and multi-step but low-risk work.
- Use frontier models for architecture, ambiguity, high-risk domains, and final synthesis.
- Spawn parallel workers only when tasks are independent and scopes are disjoint.
- Workers receive compact briefs and return compact result packets.
- For task repos with GitHub remotes, route verified save-points to the lightweight repo-maintainer worker; skip repo maintenance when no GitHub remote exists.

## Commands

```bash
./te delegate models
./te delegate classify "task"
./te delegate plan "task"
```

Implementation lives in `token_economy/delegate.py`.
