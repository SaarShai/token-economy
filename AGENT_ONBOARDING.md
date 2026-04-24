# Agent Onboarding

Use Token Economy in this repo only. The repo-local markdown wiki is the source of truth.

## Fresh Setup

If the current folder does not contain `token-economy.yaml`, clone the canonical source into the current folder:

```bash
git clone https://github.com/SaarShai/token-economy.git .
```

If the folder is not empty and cloning into `.` fails, stop and report. Do not move or delete user files.

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
- Checkpoint or fresh-start near 20% context.

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
