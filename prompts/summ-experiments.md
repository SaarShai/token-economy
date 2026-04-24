# summ Experiments

Use these only to test a host. Do not assume they work across agents.

## Goal

Find whether a host can reduce context without relying on automatic end-of-window compaction.

## Measurement

Before and after each experiment, record:

```bash
./te context status
./te context host-controls --agent auto
```

If the host has a native meter, also record it:

- Claude Code: `/context` or `/cost` when available.
- Codex CLI: `/status`.
- Gemini CLI: `/stats` when available.

Success means the host-reported active context drops or a new conversation/session starts. A nice handoff alone is not success.

## Experiments

### A. Handoff Then User New Session

1. Send `summ`.
2. Agent writes the handoff and stops.
3. User runs the host fresh-session command.
4. User pastes only the handoff plus `start.md` instruction.

Expected: reliable in every host.

### B. Native Compact

1. Send `summ`.
2. Agent writes the handoff and stops.
3. User runs host compact command: Claude `/compact`, Codex `/compact`, Gemini `/compress`.
4. Continue only if the compacted state includes the handoff and excludes old transcript noise.

Expected: useful continuation, but less clean than a new session.

### C. Native Clear/New

1. Send `summ`.
2. Agent writes the handoff and stops.
3. User runs host clear/new command: Claude `/clear`, Codex `/new` or `/clear`, Gemini new chat/session.
4. User pastes only the handoff plus `start.md` instruction.

Expected: best clean reset when the host supports it.

### D. Agent-Initiated Slash Command Probe

Ask the agent to output only the slash command, for example `/new`.

Expected: usually fails; the host treats it as assistant text, not a user/host control. Record as unsupported unless the active context actually drops.

### E. Hook/Tool Continuity

Use hooks or external tools such as `context-mode`, `token-optimizer`, `rtk`, `claude-context`, or `code-review-graph` to keep bulky outputs outside the transcript.

Expected: reduces future context growth and improves recovery, but does not itself clear the current host context.

### F. Fresh Successor Process

1. Send `summ`.
2. Agent writes the handoff and stops.
3. Run:

```bash
./te context fresh-command --agent auto --handoff <handoff-file>
```

4. Start the printed command in a terminal/new host session.

Expected: reliable workaround. The old transcript remains full, but the successor agent starts with fresh context containing only `start.md` plus the handoff.
