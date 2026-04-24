---
type: project
axis: context-refresh
tags: [context-refresh, codex, claude, handoff]
confidence: high
evidence_count: 4
---

# Host context controls

## Current truth

Token Economy can prepare lean handoffs and durable wiki memory, but the host controls whether the active model context is actually cleared.

Claude Code has a native `/clear` command. The Claude `summ` procedure should summarize current work, document durable memory, create the handoff, run or ask the user to run `/clear`, then load only `start.md` plus the handoff.

Codex in the tested Desktop/App Server environment did not expose a reliable in-thread clear from inside the assistant. The direct App Server current-thread compact path was tested against `CODEX_THREAD_ID`: `thread/resume` and `thread/compact/start` succeeded, but `thread/compacted` did not emit. The error was:

```text
Invalid Value: 'tools.defer_loading'. Deferred tools require tools.tool_search.
```

So Codex same-thread clearing/compaction must not be presented as solved. Treat `./te context codex-compact-thread` as experimental unless a future host-specific test proves reliability. The verified Codex workaround is a persistent fresh successor thread via App Server `thread/start` plus `turn/start`, seeded only with `start.md` and a handoff. This starts a clean continuation but does not reduce the old visible thread's context meter.

## Operational rule

- For Claude: use native `/clear` for a real context clear.
- For Codex: say plainly that current-thread clear is not solved in this environment. Use a fresh successor only when the goal is clean continuation, not visible-thread clearing.
- Do not ask agents in older repos to load `prompts/summ-codex-manual.md`; that file may not exist there. If a Codex successor is needed, paste the full inline launcher.
