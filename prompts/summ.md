# summ

Use when the user says `summ` or asks for a manual context refresh.

Goal: preserve continuity with the smallest useful fresh context, while a cheap worker records durable memory in the repo-local wiki. `summ` is universal up to the handoff, then platform-specific for the actual context reset/successor. The model cannot assume every host clears context the same way.

## Protocol

1. Stop new task work immediately.
2. Split session information into two buckets:
   - Fresh handoff: only goal, current state, completed work, next steps, blockers, touched paths, exact errors/commands, and links needed to continue.
   - Durable wiki memory: reusable facts, decisions, source summaries, solved workflows, and lessons that may matter later but are not needed in fresh context.
3. Treat any extra instructions after `summ` as next-session requirements. Put them in the handoff; do not execute or expand them in the old context.
4. Spawn or route a lightweight documentation worker using `prompts/subagents/wiki-documenter.prompt.md` when durable wiki memory exists. Give it only verified evidence and repo-local wiki targets. If that file is missing, use the prompt contract inline; do not spend context searching for substitutes.
5. Create the fresh handoff with `./te context checkpoint --handoff-template` or `prompts/summarize-for-handoff.md`. If the generated checkpoint is generic, replace it with a specific handoff from current session facts.
6. Keep the handoff under 2000 estimated tokens. Do not paste transcript, raw logs, broad wiki pages, or docs-only discoveries.
7. If possible, lint it with `./te context lint-handoff <handoff-file>`.
8. Check host controls with `./te context host-controls --agent auto` and choose the returned platform strategy. Also get a successor launch command with `./te context fresh-command --agent auto --handoff <handoff-file>`.
9. Codex strategy: prefer `./te context codex-fresh-thread --handoff <handoff-file> --execute` when available. This creates a persistent fresh project thread by default. Set `TOKEN_ECONOMY_CODEX_FRESH_MODEL` or pass `--model` if the host default model is unavailable. Treat it as successful only when it reports `ok: true`, `thread_persistent: true`, `thread_turns_empty: true`, `assistant_responded: true`, `thread_idle: true`, and ideally `listed_after_start: true`.
10. Claude strategy: prefer native `/clear` for a fresh context, then load only `start.md` plus the handoff. Use `/compact <handoff focus>` when preserving same-chat continuity matters. If a SlashCommand/SDK tool is exposed, invoke it there; otherwise ask the user/host to run it.
11. Gemini/Cursor/generic strategy: use the host's native compress/new-chat command when available; otherwise start a fresh session manually with only `start.md` plus the handoff.
12. Do not continue old-context work after the handoff. Prefer a fresh successor session/process when slash commands cannot be invoked directly.
13. Tell the user exactly what command to run or paste. Do not output a slash command expecting it to execute unless the host explicitly provides a tool for that.
14. End the old-context response after the handoff with: `FRESH CONTEXT PACKET READY - STOP HERE`.
15. Fresh session starts in plan mode, thinks step by step, and creates a robust plan before executing.

## Ready Prompt

```text
summ

Refresh context now. First split this session into:
1. a lean fresh-context handoff containing only what is needed to continue, and
2. durable wiki memory that should be documented but not loaded into the fresh context unless needed later.

Treat any instructions after this `summ` prompt as requirements for the fresh session. Put them in the handoff as next-session work. Do not execute them or expand them into a large plan in this old context.

Spawn or route a lightweight documentation subagent for the durable wiki memory using `prompts/subagents/wiki-documenter.prompt.md`. It should update only the repo-local wiki/log after verified evidence and return a compact result packet. If that prompt file is missing, use this contract inline and do not search broadly for substitutes.

Create the fresh handoff using `./te context checkpoint --handoff-template` or `prompts/summarize-for-handoff.md`. If the generated checkpoint is generic, replace it with a specific handoff from current session facts. Keep it under 2000 estimated tokens. Preserve exact paths, commands, decisions, and errors. Exclude transcript noise, raw logs, broad wiki pages, and docs-only discoveries.

Then check `./te context host-controls --agent auto` and choose the returned platform strategy. Also run `./te context fresh-command --agent auto --handoff <handoff-file>`. If running in Codex and App Server is available, use `./te context codex-fresh-thread --handoff <handoff-file> --execute` to start a persistent fresh successor thread in this project; pass `--model <available-model>` if needed. Treat the App Server path as successful only if it reports `ok: true`, `thread_persistent: true`, `thread_turns_empty: true`, `assistant_responded: true`, `thread_idle: true`, and ideally `listed_after_start: true`. If running in Claude Code, use `/clear` or `/compact` through a real host/SlashCommand tool if one is available; otherwise ask me to run it and stop. Do not assume you can execute host slash commands from your own response. Tell me the exact command I or the host should run and exactly what to paste next. Do not load anything else until retrieval proves relevance.

End your old-context response immediately after the handoff with:
FRESH CONTEXT PACKET READY - STOP HERE

In the fresh context, start in plan mode. Think step by step. Create a robust plan before executing.
```
