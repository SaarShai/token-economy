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

### G. Codex App Server Fresh Thread

Use when Codex slash-command text does not execute and `codex app-server` is available.

1. Create or choose a handoff file.
2. Dry-run the successor plan:

```bash
./te context codex-fresh-thread --handoff <handoff-file> --model gpt-5.3-codex-spark
```

3. Execute it:

```bash
./te context codex-fresh-thread --handoff <handoff-file> --model gpt-5.3-codex-spark --execute
```

Expected: App Server creates an ephemeral thread with `turns: []`, starts a turn in that thread, receives an assistant response, and returns idle. The JSON should report `ok: true`, `thread_ephemeral: true`, `thread_turns_empty: true`, `assistant_responded: true`, and `thread_idle: true`. This is a real fresh successor context, not an in-place clear of the old transcript. If it fails with "model does not exist or you do not have access," rerun with an available model or set `TOKEN_ECONOMY_CODEX_FRESH_MODEL`. Large input-token counts can come from Codex host/system/tool context; they do not by themselves prove that the old transcript was loaded.

Verified controlled `summ` result on 2026-04-24:

```bash
./te context codex-fresh-thread --handoff .token-economy/checkpoints/20260424-135455-fresh-session.md --model gpt-5.3-codex-spark --execute
```

Result: `ok=true`, `thread_id=019dbfc5-edbe-7632-9a51-0dda81340fb0`, `assistant_responded=true`, and `thread_idle=true`. Events showed `thread/started` with `ephemeral=true` and `turns=[]`; the successor read `start.md` plus the handoff only. The old visible host transcript was not erased. Token usage still included large Codex host/system overhead, about 53k input tokens, despite no old transcript in the successor-visible prompt.
