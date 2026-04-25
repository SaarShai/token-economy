# Optional External Adapters

Token Economy learns from these projects but does not vendor their code by default.

## Terminal And Tool Output

- `omni`: terminal-output filtering. Learned patterns now adopted natively: raw-output recovery, savings stats, custom rules, and opt-in session-aware suppression. Keep Omni external for host-specific cases.
- `rtk`: Rust CLI proxy for common dev commands. Useful for fast command-output reduction.
- `context-mode`: sandboxed tool output plus SQLite continuity. Useful for hook-capable platforms.

## Codebase Retrieval

- `code-review-graph`: tree-sitter code graph. Useful for large code review and symbol-aware navigation.
- `claude-context`: hybrid code search MCP. Useful when semantic code search matters more than zero-dependency setup.

## Markdown Wiki Retrieval

- `qmd`: markdown BM25/vector search. Useful once wiki scale exceeds simple FTS/grep comfort.

## Policy

- Install only when `./te doctor` shows a matching pain.
- Keep `start.md` and adapters lean; document optional installs here.
- Do not vendor third-party code unless a future review explicitly approves license, maintenance, and security tradeoffs.
