---
name: relay-sessions
description: Use when the user asks to relay, hand off, summarize, continue in a fresh Codex session, or let a new session ask an old/older session targeted follow-up questions.
---

# Relay Sessions

Use the repo-local `relay_session` package to create compact handoffs and launch fresh Codex successor sessions.

## Rules

- Keep handoffs under 2K estimated tokens.
- Read `start.md` plus the handoff only in the successor.
- Do not load broad archives unless retrieval proves relevance.
- Narrow repo retrieval means targeted reads/searches of known files, status, or symbols; it does not mean loading broad archives.
- Ask old sessions only for specific missing facts after narrow repo retrieval is insufficient.
- If the old session identifies an even older relay handoff as the source, repeat `ask-old` with that older handoff and the same narrow question.
- Treat UI visibility as user-confirmed; backend `listed_after_start: true` proves app-server listing, not immediate sidebar rendering.

## Commands

Create a handoff only:

```bash
python3 -m relay_session.cli --repo "$PWD" checkpoint \
  --goal "<current task and critical facts>" \
  --plan "<next step>"
```

Launch a fresh successor:

```bash
python3 -m relay_session.cli --repo "$PWD" relay \
  --goal "<current task and critical facts>" \
  --name "<session name>" \
  --version 01 \
  --execute
```

Visibility or handoff-quality tests should stop after verification:

```bash
python3 -m relay_session.cli --repo "$PWD" relay \
  --goal "<test goal>" \
  --name "<session name>" \
  --version 01 \
  --execute \
  --stop-after-verify
```

Ask the old session:

```bash
python3 -m relay_session.cli --repo "$PWD" ask-old \
  --handoff <handoff-file> \
  --question "<specific missing fact>" \
  --execute
```

Omit `--execute` to dry-run routing and confirm which old thread/transcript would be queried.
Add `--execute` to actually ask the old session.
