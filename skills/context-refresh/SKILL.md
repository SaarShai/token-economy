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
3. Route a lightweight/cheap/smaller-model wiki-documenter with `prompts/subagents/wiki-documenter.prompt.md`.
4. Create handoff with `./te context checkpoint --handoff-template` or `prompts/summarize-for-handoff.md`; replace generic output with session-specific facts. For manual copy-paste refresh, write repo-root `session_handoff.md`.
5. Prefer cheapest capable summarizer worker for the handoff; it returns only the packet.
6. Lint the handoff with `./te context lint-handoff <handoff-file>`.
7. Fresh session reads handoff + `start.md` only, enters plan-first mode, then retrieves on demand.

Hard rules:
- Handoff <= 2000 estimated tokens.
- Do not paste full transcript into fresh session.
- Do not load docs-only wiki memory into fresh context; link to it instead.
- Do not execute first in fresh session.
- A handoff without a fresh context is not a completed refresh; use `prompts/summ-experiments.md` to test hosts.
- Manual copy-paste prompts live at `prompts/manual-summ-document-and-handoff.md` and `prompts/manual-fresh-session-from-handoff.md`.
