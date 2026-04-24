# Context Host Controls

Use during `summ`, checkpoint, or manual refresh.

Token Economy can create the handoff packet and durable memory updates. The host app controls the actual context reset.

## Native Controls

| Host | Compact summary | Fresh context | Status |
|---|---|---|---|
| Claude Code | `/compact` | `/clear`, then paste handoff + `start.md` | `/context` or `/cost` when available |
| Claude SDK | dispatch `/compact` | end current query and start a new one | SDK init/usage metadata |
| Codex CLI | `/compact` | `/new`, or `/clear` then paste handoff + `start.md` | `/status` |
| Gemini CLI | `/compress` | new chat/session; `/clear` behavior varies by version | `/stats` when available |
| Generic | host compact/compress | host new-chat/new-session | host meter |

## Rule

After `summ` writes the handoff:

1. Prefer host-native fresh context when available.
2. Load only the handoff packet plus `start.md`.
3. Do not continue old-context task work.
4. If native clear cannot be invoked by the agent, tell the user the exact command to run and stop.

Check current host guidance:

```bash
./te context host-controls --agent auto
```

## External Context Tools

Tools such as `context-mode`, `token-savior`, `token-optimizer`, `claude-context`, `code-review-graph`, and `rtk` reduce what enters context or preserve state around compaction. They are useful companions, but they do not replace the host-native clear/new-chat control.
