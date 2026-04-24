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
4. If durable memory exists, route a lightweight/cheap/smaller-model wiki-documenter with `prompts/subagents/wiki-documenter.prompt.md`; if missing, use the contract inline.
5. Create handoff with `./te context checkpoint --handoff-template` or `prompts/summarize-for-handoff.md`; replace generic output with session-specific facts. For manual copy-paste refresh, write repo-root `session_handoff.md`.
6. Prefer cheapest capable summarizer worker for the handoff; it returns only the packet.
7. Check host controls with `./te context host-controls --agent auto`; get a successor launch command with `./te context fresh-command --agent auto --handoff <handoff-file>`.
8. Clear or bypass old context using the selected host strategy. Claude Code `/clear` is the practical manual clear path. Codex current-thread clear/compact is unsolved in the tested Desktop/App Server environment; `./te context codex-compact-thread` is experimental only. Use `./te context codex-fresh-thread --handoff <handoff-file> --execute` as clean-continuation workaround, not as old-thread clearing.
9. Treat native clear/compact/new-chat as a user/host action unless a real host tool exists; prefer a fresh successor process when direct clear is unavailable.
10. Fresh session reads handoff + `start.md` only, enters plan-first mode, then retrieves on demand.

Hard rules:
- Handoff <= 2000 estimated tokens.
- Do not paste full transcript into fresh session.
- Do not load docs-only wiki memory into fresh context; link to it instead.
- Do not execute first in fresh session.
- If host cannot clear context or compact through a real tool, emit the handoff and stop with `FRESH CONTEXT PACKET READY - STOP HERE`.
- A handoff without a host context drop is not a completed refresh; use `prompts/summ-experiments.md` to test hosts.
- Manual copy-paste prompts live at `prompts/manual-summ-document-and-handoff.md` and `prompts/manual-fresh-session-from-handoff.md`.
