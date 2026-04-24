# Manual summ: document + handoff

Copy-paste this into the current/old session when you need a manual Token Economy refresh and will start a fresh session yourself.

```text
summ

Goal: summarize the current session, document durable memory to the repo-local wiki with a cheap/smaller-model worker, and write `session_handoff.md` at the repo root.

Work only inside the repo root containing `token-economy.yaml`.

Protocol:
1. Read only the minimal framework files needed for refresh: `start.md`, `prompts/summarize-for-handoff.md`, and `prompts/subagents/wiki-documenter.prompt.md`.
2. Split session information into two buckets:
   - Fresh handoff: only goal, current state, completed work, in-progress work, blockers, next steps, touched paths, exact commands/errors, key decisions, wiki links, and retrieval pointers needed by the next session.
   - Durable wiki memory: verified reusable facts, decisions, source summaries, solved workflows, or lessons that may matter later but are not needed in fresh context.
3. Spawn or route a lightweight/cheap/smaller-model wiki-documenter using `prompts/subagents/wiki-documenter.prompt.md`. Give it only verified evidence, exact source paths/commands/errors when relevant, and candidate repo-local wiki targets. It must update only the repo-local wiki/log and return a compact result packet. If subagents are unavailable, perform only the minimum wiki/log update yourself.
4. Create `session_handoff.md` at the repo root using the structure from `prompts/summarize-for-handoff.md`. Keep it under 2000 estimated tokens. Preserve exact paths, commands, errors, decisions, blockers, commits, active unfinished subagents, and next-session requirements. Exclude transcript noise, raw logs, broad wiki pages, docs-only discoveries, and large plans that should be rebuilt in fresh context.
5. In `session_handoff.md`, link to wiki pages updated by the documenter but do not inline their contents unless they are immediately required to continue.
6. Run:
   `./te context lint-handoff session_handoff.md`
   Fix only handoff-format issues. Do not broaden the packet.
```
