---
name: context-keeper
description: PreCompact hook for structured state preservation before compaction. Use when the host can chain project-local PreCompact hooks.
tools: Bash, Read, Write
model: haiku
---

# context-keeper — structured memory before compaction

Use the lightweight pre-compact hook to preserve file paths, commands, errors, and decisions before context compression.

## Install

```bash
bash projects/context-keeper/install.sh --project
```

## Hook

- The project-local hook lives at `projects/context-keeper/hook.sh`.
- The hook writes a structured memory packet via `./te context checkpoint`.
- Chain it from project-local `.claude/settings.json` under `PreCompact`.

## Rules

- Do not load the full transcript in the hook.
- Keep the output terse.
- Preserve exact paths, commands, numbers, and error strings.
