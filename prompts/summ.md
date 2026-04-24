# summ

Use when the user says `summ` or asks for a manual context refresh.

Goal: preserve continuity with the smallest useful fresh context, while a cheap worker records durable memory in the repo-local wiki.

## Protocol

1. Stop new task work.
2. Split session information into two buckets:
   - Fresh handoff: only goal, current state, completed work, next steps, blockers, touched paths, exact errors/commands, and links needed to continue.
   - Durable wiki memory: reusable facts, decisions, source summaries, solved workflows, and lessons that may matter later but are not needed in fresh context.
3. Spawn or route a lightweight documentation worker using `prompts/subagents/wiki-documenter.prompt.md` when durable wiki memory exists. Give it only verified evidence and repo-local wiki targets.
4. Create the fresh handoff with `./te context checkpoint --handoff-template` or `prompts/summarize-for-handoff.md`.
5. Keep the handoff under 2000 estimated tokens. Do not paste transcript, raw logs, broad wiki pages, or docs-only discoveries.
6. If possible, lint it with `./te context lint-handoff <handoff-file>`.
7. Clear/compact the current context. If the host cannot clear context programmatically, open a fresh session.
8. Load only the handoff packet and `start.md` into the fresh context. Retrieve anything else on demand.
9. Fresh session starts in plan mode, thinks step by step, and creates a robust plan before executing.

## Ready Prompt

```text
summ

Refresh context now. First split this session into:
1. a lean fresh-context handoff containing only what is needed to continue, and
2. durable wiki memory that should be documented but not loaded into the fresh context unless needed later.

Spawn or route a lightweight documentation subagent for the durable wiki memory using `prompts/subagents/wiki-documenter.prompt.md`. It should update only the repo-local wiki/log after verified evidence and return a compact result packet.

Create the fresh handoff using `./te context checkpoint --handoff-template` or `prompts/summarize-for-handoff.md`. Keep it under 2000 estimated tokens. Preserve exact paths, commands, decisions, and errors. Exclude transcript noise, raw logs, broad wiki pages, and docs-only discoveries.

Then clear/compact this context. If you cannot clear context programmatically, start a fresh session with only the handoff packet plus `start.md`. Do not load anything else until retrieval proves relevance.

In the fresh context, start in plan mode. Think step by step. Create a robust plan before executing.
```
