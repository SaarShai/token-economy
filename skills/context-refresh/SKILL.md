---
name: context-refresh
description: Refresh context at 20 percent fill or on explicit refresh request.
---

# Context Refresh

Trigger:
- `te context meter` action is `refresh`
- user says `summ`
- user asks `/refresh`
- host context feels stale or overloaded

Protocol:
1. Run `./te context meter --transcript <file>` when transcript path exists.
2. Split information into fresh-handoff material versus durable wiki memory.
3. If durable memory exists, route a lightweight wiki-documenter with `prompts/subagents/wiki-documenter.prompt.md`.
4. Create handoff with `./te context checkpoint --handoff-template` or `prompts/summarize-for-handoff.md`.
5. Prefer cheapest summarizer worker for the handoff; it returns only the packet.
6. Write packet before clearing/compacting.
7. Fresh session reads handoff + `start.md` only, enters plan-first mode, then retrieves on demand.

Hard rules:
- Handoff <= 2000 estimated tokens.
- Do not paste full transcript into fresh session.
- Do not load docs-only wiki memory into fresh context; link to it instead.
- Do not execute first in fresh session.
