# Agent Onboarding

Use Token Economy in the current target repo only. The repo-local markdown wiki is the source of truth.

## Fresh Setup

For a fresh target folder, clear the current folder only, including hidden files and `.git`, then retrieve the downstream runtime/framework files:

```bash
find . -mindepth 1 -maxdepth 1 -exec rm -rf {} +
git clone --depth 1 --filter=blob:none --sparse https://github.com/SaarShai/token-economy.git .
git sparse-checkout set --no-cone \
  '/.gitignore' '/AGENTS.md' '/CLAUDE.md' '/GEMINI.md' '/INSTALL.sh' \
  '/L0_rules.md' '/L1_index.md' '/LICENSE' '/index.md' '/models.yaml' \
  '/schema.md' '/start.md' '/te' '/token-economy.yaml' \
  '/token_economy/*' '/adapters/*' '/hooks/*' '/hooks/output-filter/*' \
  '/prompts/*.md' '/prompts/subagents/*' \
  '/skills/caveman-ultra/*' '/skills/context-refresh/*' \
  '/skills/personal-assistant/*' '/skills/plan-first-execute/*' \
  '/skills/subagent-orchestrator/*' '/skills/verification-before-completion/*' \
  '/skills/wiki-retrieve/*' '/skills/wiki-write/*' '/templates/*'
rm -rf .git
git init
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

- Work only inside the current working folder for the active project. If this framework is being bootstrapped into a new folder, that folder is the workspace.
- Do not edit home-directory agent settings, machine-wide config, global MCP config, or external wikis.
- Use the repo-local markdown wiki: `raw/`, `concepts/`, `patterns/`, `projects/`, `people/`, `queries/`, `L0_rules.md`, `L1_index.md`, `L2_facts/`, `L3_sops/`, `L4_archive/`.
- Use interlinked markdown pages with real wiki IDs such as `[[start]]` or `[[projects/example/README]]`.
- Retrieve before reasoning with `./te wiki search`, then `./te wiki timeline <id>`, then `./te wiki fetch <id>`.
- Document only after verified work, and only in repo-local wiki pages and `log.md`.
- Use `/pa` for context-light prompts.
- Keep normal prompt hooks quiet unless `TOKEN_ECONOMY_CLASSIFY_ALL=1` is explicitly set.
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
