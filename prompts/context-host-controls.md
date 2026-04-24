# Context Host Controls

Use during `summ`, checkpoint, or manual refresh.

Token Economy can create the handoff packet and durable memory updates. The host app controls the actual context reset. Do not assume the model can execute host slash commands from its own assistant message.

## Native Controls

| Host | Compact summary | Fresh context | Status |
|---|---|---|---|
| Claude Code | `/compact` | `/clear`, then paste handoff + `start.md` | `/context` or `/cost` when available |
| Claude SDK | dispatch `/compact` | end current query and start a new one | SDK init/usage metadata |
| Codex CLI | `/compact` | `/new` or `/clear` when host accepts it; programmatic successor via `./te context codex-fresh-thread` | `/status` |
| Gemini CLI | `/compress` | new chat/session; `/clear` behavior varies by version | `/stats` when available |
| Generic | host compact/compress | host new-chat/new-session | host meter |

## Rule

After `summ` writes the handoff:

1. Prefer host-native fresh context when available.
2. Load only the handoff packet plus `start.md`.
3. Do not continue old-context task work.
4. Treat native slash commands as user/host actions unless the host exposes a real tool for invoking them.
5. If slash commands cannot be invoked, use a fresh successor process/session. For Codex, prefer the App Server fresh-thread path.
6. Tell the user the exact command to run and stop.

Check current host guidance:

```bash
./te context host-controls --agent auto
./te context fresh-command --agent auto --handoff <handoff-file>
./te context codex-fresh-thread --handoff <handoff-file>
```

## Workarounds

Best practical workaround: launch a fresh successor session with only `start.md` and the handoff file. This does not clear the current transcript; it bypasses it.

Examples:

```bash
codex -C "$PWD" "Read $PWD/start.md and <handoff-file> only. Continue from that handoff. Start in plan mode."
claude --add-dir "$PWD" "Read $PWD/start.md and <handoff-file> only. Continue from that handoff. Start in plan mode."
gemini --prompt-interactive "Read $PWD/start.md and <handoff-file> only. Continue from that handoff. Start in plan mode."
```

For Codex hosts with App Server support, Token Economy can start a fresh ephemeral successor thread directly:

```bash
./te context codex-fresh-thread --handoff <handoff-file> --model gpt-5.3-codex-spark --execute
```

Use `TOKEN_ECONOMY_CODEX_FRESH_MODEL=<model>` to change the default. Success means the command reports `ok: true`, `thread_ephemeral: true`, `thread_turns_empty: true`, `assistant_responded: true`, and `thread_idle: true`. The old host transcript is not erased; the fresh thread bypasses it. Codex may still show large input-token counts from host/system/tool context, but that is not evidence that the old transcript was loaded.

Other possible but brittle workarounds:

- Terminal automation such as `tmux send-keys` or `osascript` can type `/new`, `/clear`, `/compact`, or `/compress` into a host UI, but only when the session is in a known terminal/pane.
- Host hooks can preserve/restore state around compaction, but usually cannot initiate compaction.
- Successor subagents can continue work in a fresh worker context, but the user may still need a new main chat for interactive control.

## External Context Tools

Tools such as `context-mode`, `token-savior`, `token-optimizer`, `claude-context`, `code-review-graph`, and `rtk` reduce what enters context or preserve state around compaction. They are useful companions, but they do not replace the host-native clear/new-chat control.

For host-specific trials, use `prompts/summ-experiments.md`.
