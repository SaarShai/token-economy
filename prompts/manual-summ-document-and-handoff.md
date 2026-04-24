# Manual summ: document + handoff

Copy-paste this into the current/old session when you need a manual Token Economy refresh and will start a fresh session yourself.

```text
summ

Refresh context now. This is a Token Economy context-refresh operation only.

Goal: summarize the current session, document durable memory to the repo-local wiki with a cheap/smaller-model worker when available, write `session_handoff.md` at the repo root, then stop so I can clear/bypass the old context and start fresh.

Work only inside the repo root containing `token-economy.yaml`.

Protocol:
1. Stop new task work immediately. Treat any instructions after this prompt as next-session requirements. Put them in `session_handoff.md`; do not execute them in this old context.
2. Read only the minimal framework files needed for refresh: `start.md`, `prompts/summarize-for-handoff.md`, `prompts/subagents/wiki-documenter.prompt.md` if present, and host-control guidance only if needed.
3. Split session information into two buckets:
   - Fresh handoff: only goal, current state, completed work, in-progress work, blockers, next steps, touched paths, exact commands/errors, key decisions, wiki links, and retrieval pointers needed by the next session.
   - Durable wiki memory: verified reusable facts, decisions, source summaries, solved workflows, or lessons that may matter later but are not needed in fresh context.
4. If durable wiki memory exists, spawn or route a lightweight/cheap/smaller-model wiki-documenter using `prompts/subagents/wiki-documenter.prompt.md`. Give it only verified evidence, exact source paths/commands/errors when relevant, and candidate repo-local wiki targets. It must update only the repo-local wiki/log and return a compact result packet. If subagents are unavailable, perform only the minimum wiki/log update yourself. If the prompt file is missing, use this inline contract and do not search broadly for substitutes.
5. Create `session_handoff.md` at the repo root using the structure from `prompts/summarize-for-handoff.md`. Keep it under 2000 estimated tokens. Preserve exact paths, commands, errors, decisions, blockers, commits, active unfinished subagents, and next-session requirements. Exclude transcript noise, raw logs, broad wiki pages, docs-only discoveries, and large plans that should be rebuilt in fresh context.
6. In `session_handoff.md`, link to wiki pages updated by the documenter but do not inline their contents unless they are immediately required to continue.
7. If available, run:
   `./te context lint-handoff session_handoff.md`
   Fix only handoff-format issues. Do not broaden the packet.
8. State the host action needed:
   - Claude Code: run `/clear`, then paste the fresh-session prompt with `start.md` + `session_handoff.md`.
   - Codex: current-thread clear/compact is unsolved in the tested environment; use a fresh successor/new session as clean continuation, not as clearing the old visible thread.
   - Generic: start a new session with only `start.md` + `session_handoff.md`.
9. Do not continue old-context task work after `session_handoff.md` is ready.

End the old-context response exactly with:
FRESH CONTEXT PACKET READY - STOP HERE
```
