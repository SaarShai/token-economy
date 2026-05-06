# relay-session

Standalone Codex relay sessions.

Creates lean handoffs, launches a fresh Codex successor thread with a versioned
`Relay[NN]: name`, and lets the successor ask the old session narrow follow-up
questions when the handoff intentionally omits detail.

This project is independent of Token Economy. Copy `relay_session/` into another
repo, or run it in place.

## Commands

```bash
python3 -m relay_session.cli checkpoint --repo "$PWD" --goal "continue work"
python3 -m relay_session.cli launch --repo "$PWD" --handoff .relay-session/checkpoints/<file>.md --name "Setting Up Relay" --version 01 --execute
python3 -m relay_session.cli ask-old --repo "$PWD" --handoff .relay-session/checkpoints/<file>.md --question "What exact decision was made?" --execute
```

`ask-old` is explicit-only by design. The successor should retrieve from repo
state first, then ask the old session only for a specific missing fact.

## Handoff Contract

Relay handoffs include:

- `old-thread-id`
- `old-transcript`
- `old-session-query-policy: explicit-only`
- required sections 1-9
- a successor instruction to ask old only when repo retrieval is insufficient

## Requirements

- Python 3.9+
- Codex CLI only for `launch --execute` and `ask-old --execute`

