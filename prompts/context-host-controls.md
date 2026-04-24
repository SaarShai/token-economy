# Context Host Controls

Use during `summ`, checkpoint, or manual refresh.

Token Economy uses one universal refresh protocol and host-specific execution profiles. The universal part is: summarize, document durable memory, write a lean handoff, then continue from only `start.md` plus that handoff. The host-specific part is how the fresh/compact context is actually created.

Do not assume every model/platform can clear context the same way. The agent must pick the right profile with `./te context host-controls --agent auto`.

## Native Controls

| Host | Strategy | Compact summary | Fresh context | Status |
|---|---|---|---|---|
| Claude Code | native clear/compact | `/compact` | `/clear`, then paste handoff + `start.md` | `/context` or `/cost` when available |
| Claude SDK | slash-command dispatch | dispatch `/compact` | dispatch `/clear` or end query and start a new one | SDK init/usage metadata |
| Codex CLI/Desktop | compact current thread or persistent successor thread | `./te context codex-compact-thread --current --execute` or `/compact` | `./te context codex-fresh-thread --execute` or `codex fork --last` | `/status` |
| Gemini CLI | native compress/new session | `/compress` | new chat/session; `/clear` behavior varies by version | `/stats` when available |
| Cursor | new chat with handoff | host compact if available | new chat with only handoff + `start.md` | host meter |
| Generic | manual fresh session | host compact/compress | host new-chat/new-session | host meter |

## Rule

After `summ` writes the handoff:

1. Run `./te context host-controls --agent auto`.
2. Choose the returned `strategy`, not a generic guess.
3. Load only the handoff packet plus `start.md` in the fresh/compacted context.
4. Do not continue old-context task work after emitting or launching the successor.
5. Treat native slash commands as user/host actions unless the host exposes a real tool for invoking them.
6. Tell the user the exact command to run when the host action cannot be invoked programmatically.

Check current host guidance:

```bash
./te context host-controls --agent auto
./te context fresh-command --agent auto --handoff <handoff-file>
./te context codex-compact-thread --current --handoff <handoff-file>
./te context codex-fresh-thread --handoff <handoff-file>
```

If an older project-local `te` does not have `host-controls`, `fresh-command`, `codex-compact-thread`, or `codex-fresh-thread`, do not treat `./te context fresh-start` as a launcher. It only writes or prints a packet. For Codex, try direct `codex app-server` first: compact `CODEX_THREAD_ID` with `thread/compact/start` if same-session continuity matters, or start a persistent successor thread if a clean bypass matters. Only if App Server fails, use a host-native new session, `codex fork --last -C "$PWD" "<handoff instruction>"`, or `codex -C "$PWD" "<handoff instruction>"`.

## Workarounds

Best practical workaround for hosts without callable clear: launch a fresh successor session with only `start.md` and the handoff file. This does not clear the current transcript; it bypasses it.

For older Codex installs where the Token Economy wrapper is not present but `codex app-server` exists, use App Server directly. For compact, resume `CODEX_THREAD_ID` with a custom `compact_prompt`, send `thread/compact/start`, and wait for `thread/compacted`. For a fresh successor, create a persistent `thread/start` with `ephemeral: false`, send a single `turn/start` containing only the handoff instruction, and wait for idle or a clear error. Do not stop after merely printing `codex fork` unless App Server is unavailable or failed.

Examples:

```bash
codex -C "$PWD" "Read $PWD/start.md and <handoff-file> only. Continue from that handoff. Start in plan mode."
codex fork --last -C "$PWD" "Read $PWD/start.md and <handoff-file> only. Continue from that handoff. Start in plan mode."
claude --add-dir "$PWD" "Read $PWD/start.md and <handoff-file> only. Continue from that handoff. Start in plan mode."
gemini --prompt-interactive "Read $PWD/start.md and <handoff-file> only. Continue from that handoff. Start in plan mode."
```

For Codex hosts with App Server support, Token Economy can start a persistent fresh successor thread directly:

```bash
./te context codex-compact-thread --current --handoff <handoff-file> --execute
./te context codex-fresh-thread --handoff <handoff-file> --model gpt-5.3-codex-spark --execute
```

For compaction, success means `ok: true`, `resume_ok: true`, `compact_start_ok: true`, and `compacted: true`. For fresh successor, use `--ephemeral` only for throwaway smoke tests. Use `TOKEN_ECONOMY_CODEX_FRESH_MODEL=<model>` to change the default. Success means the command reports `ok: true`, `thread_persistent: true`, `thread_turns_empty: true`, `assistant_responded: true`, `thread_idle: true`, and ideally `listed_after_start: true`. The fresh thread bypasses rather than erases the old host transcript. Codex may still show large input-token counts from host/system/tool context; that is not evidence that the old transcript was loaded.

For Claude Code, prefer native controls:

```text
/clear
```

Then load only the handoff plus `start.md`. Use `/compact <handoff focus>` when same-chat continuity matters more than a fully fresh context. If a SlashCommand/SDK tool is exposed, the agent may invoke the command through that tool; otherwise it must ask the user/host to run the command.

Other possible but brittle workarounds:

- Terminal automation such as `tmux send-keys` or `osascript` can type `/new`, `/clear`, `/compact`, or `/compress` into a host UI, but only when the session is in a known terminal/pane.
- Host hooks can preserve/restore state around compaction, but usually cannot initiate compaction.
- Successor subagents can continue work in a fresh worker context, but the user may still need a new main chat for interactive control.

## External Context Tools

Tools such as `context-mode`, `token-savior`, `token-optimizer`, `claude-context`, `code-review-graph`, and `rtk` reduce what enters context or preserve state around compaction. They are useful companions, but they do not replace the host-native clear/new-chat control.

For host-specific trials, use `prompts/summ-experiments.md`.
