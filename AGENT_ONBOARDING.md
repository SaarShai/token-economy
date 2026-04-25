# Agent Onboarding

Use Token Economy in this repo only. The repo-local markdown wiki is the source of truth.

## Fresh Setup

If the current folder does not contain `token-economy.yaml`, the setup prompt authorizes a fresh install by clearing the current folder only, including hidden files and `.git`, then cloning the canonical source:

```bash
find . -mindepth 1 -maxdepth 1 -exec rm -rf {} +
git clone https://github.com/SaarShai/token-economy.git .
```

Do not delete anything outside the current folder.
Start by writing a short step-by-step plan in chat, then execute it.

Then run:

```bash
./INSTALL.sh --dry-run
./INSTALL.sh --scope project --agent auto
./te doctor
./te hooks doctor
./te wiki search "start"
./te context status
```

## Rules

- Work only inside the repo root containing `token-economy.yaml`.
- Do not edit home-directory agent settings, machine-wide config, global MCP config, or external wikis.
- Use the repo-local markdown wiki: `raw/`, `concepts/`, `patterns/`, `projects/`, `people/`, `queries/`, `L0_rules.md`, `L1_index.md`, `L2_facts/`, `L3_sops/`, `L4_archive/`.
- Use interlinked markdown pages with real wiki IDs such as `[[start]]` or `[[projects/wiki-search/README]]`.
- Retrieve before reasoning with `./te wiki search`, then `./te wiki timeline <id>`, then `./te wiki fetch <id>`.
- Document only after verified work, and only in repo-local wiki pages and `log.md`.
- Use `/pa` for context-light prompts.
- Keep normal prompt hooks quiet unless `TOKEN_ECONOMY_CLASSIFY_ALL=1` is explicitly set.
- When maintaining this Token Economy repo and considering adoption from another repo, load `skills/token-economy-external-adoption/SKILL.md` before inspection or implementation. This workflow is project-maintenance only, not a downstream user rule.
- For framework maintenance updates, finish with verification, a commit, and a clean working tree. If cleanup or review is useful, spawn a small subagent, then merge or fix before committing.
- Checkpoint near 20% context. Use `summ` for manual refresh: lean handoff, durable memory to a lightweight wiki-documenter, then host-specific clear/fresh continuation. Claude can use native `/clear`. Codex current-thread clear is not solved in the tested environment; fresh successor is `./te context codex-fresh-thread --handoff <handoff-file> --execute`.
- If the task workspace has a GitHub remote, use the lightweight repo-maintainer worker at verified save-points; otherwise skip repo maintenance.

## Project-Local Adapters

Install adapter files only in this repo:

```bash
./te start --agent auto --scope project
```

This may create repo-local files such as `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, or `.cursor/rules/token-economy.mdc`. These are small pointers to `start.md` and the universal adapter.

## After Setup

Drop setup-only details from context. Keep only:

- repo root path
- `start.md`
- `token-economy.yaml`
- `./te` command surface
- wiki retrieval commands
- repo-local-only scope rule

Report changed files, verification results, and remaining risk.
