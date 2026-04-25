# Install Token Economy Framework

Project-local install:

```bash
./INSTALL.sh --scope project
```

Dry run:

```bash
./INSTALL.sh --dry-run
```

What it checks:
- `te doctor`
- `te hooks doctor`
- `te wiki index`
- adapter copy via `te start`
- repo-local install helpers when their files are present

## Fresh Target Project Setup

In a new empty target project folder, retrieve only the downstream runtime/framework files:

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

This permission applies only to the current target folder named by the user. Do not delete parent folders or files elsewhere.

The framework does not install global agent settings.
