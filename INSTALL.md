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

The framework does not install global agent settings. Stable measured tools remain available through `stable/INSTALL.sh` in project-local mode.
