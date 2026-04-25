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
- optional adapter copy via `te start`
- repo-local install helpers for agents-triage, context-keeper, and semdiff

## Fresh Target Project Setup

If a target project folder is meant to use Token Economy and does not contain `token-economy.yaml`, clear that folder only, then clone the framework scaffold:

```bash
find . -mindepth 1 -maxdepth 1 -exec rm -rf {} +
git clone https://github.com/SaarShai/token-economy.git .
```

This permission applies only to the current target folder named by the user. Do not delete parent folders or files elsewhere.

The clone makes the folder Token Economy-enabled. It does not mean the agent is working on the Token Economy framework project, and it does not import this repo's roadmap, handoffs, or framework-development tasks as downstream goals.

The framework does not install global agent settings. Stable measured tools remain available through `stable/INSTALL.sh` in project-local mode.
