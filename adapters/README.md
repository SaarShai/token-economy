# Agent Adapters

Tiny platform-specific startup files. They point the agent at `start.md` and keep always-loaded context lean.

## Files

- `universal/START.md` — canonical startup glue
- `claude/CLAUDE.md`
- `codex/AGENTS.md`
- `gemini/GEMINI.md`
- `cursor/token-economy.mdc`

Install project-scoped:

```bash
./te start --agent auto --scope project
```

Existing project instruction files are not overwritten. If one exists, `te start` writes a sidecar `.token-economy` adapter file.

All platform adapters are thin wrappers that point at `start.md`.

## Rule

Adapters contain only platform glue. Detailed behavior belongs in `start.md`, `schema.md`, and on-demand wiki pages.
