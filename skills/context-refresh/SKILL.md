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
3. Treat extra instructions after `summ` as next-session requirements; do not execute or expand them in the old context.
4. If durable memory exists, route a lightweight wiki-documenter with `prompts/subagents/wiki-documenter.prompt.md`; if missing, use the contract inline.
5. Create handoff with `./te context checkpoint --handoff-template` or `prompts/summarize-for-handoff.md`; replace generic output with session-specific facts.
6. Prefer cheapest summarizer worker for the handoff; it returns only the packet.
7. Check host controls with `./te context host-controls --agent auto` or `prompts/context-host-controls.md`.
8. Use native clear/compact/new-chat when available; if the agent cannot invoke it, tell the user the exact command and stop old-context work.
9. Fresh session reads handoff + `start.md` only, enters plan-first mode, then retrieves on demand.

Hard rules:
- Handoff <= 2000 estimated tokens.
- Do not paste full transcript into fresh session.
- Do not load docs-only wiki memory into fresh context; link to it instead.
- Do not execute first in fresh session.
- If host cannot clear context, emit the handoff and stop with `FRESH CONTEXT PACKET READY - STOP HERE`.
