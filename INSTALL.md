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

## Fresh Folder Setup

If a target folder is meant to become a fresh Token Economy checkout and does not contain `token-economy.yaml`, clear that folder only, then clone:

```bash
find . -mindepth 1 -maxdepth 1 -exec rm -rf {} +
git clone https://github.com/SaarShai/token-economy.git .
```

This permission applies only to the current target folder named by the user. Do not delete parent folders or files elsewhere.

The framework does not install global agent settings. Stable measured tools remain available through `stable/INSTALL.sh` in project-local mode.
