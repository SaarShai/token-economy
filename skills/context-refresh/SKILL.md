---
name: context-refresh
description: Refresh context at 20 percent fill or on explicit refresh request.
---

# Context Refresh

Trigger:
- `te context meter` action is `refresh`
- user asks `/refresh`
- host context feels stale or overloaded

Protocol:
1. Run `./te context meter --transcript <file>` when transcript path exists.
2. If refresh needed, create handoff with `./te context checkpoint --handoff-template`.
3. Prefer cheapest summarizer worker using `prompts/summarize-for-handoff.md`.
4. Write packet before clearing/compacting.
5. Fresh session reads handoff + `start.md` only, enters plan-first mode, then retrieves on demand.

Hard rules:
- Handoff <= 2000 estimated tokens.
- Do not paste full transcript into fresh session.
- Do not execute first in fresh session.

