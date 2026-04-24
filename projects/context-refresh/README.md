---
type: project
axis: cross_session_memory
tags: [context-refresh, checkpoint, compaction]
confidence: med
evidence_count: 1
---

# context-refresh

Fresh-context workflow for preventing context rot.

## Contract

- Estimate context fullness with `./te context status`.
- Default max context: detected from config/env or fallback `128000`.
- Default trigger: `refresh_threshold: 0.20`.
- At threshold, run `./te context checkpoint`.
- If the host cannot clear context programmatically, run `./te context fresh-start` and begin a new session with the emitted packet.

## Packet

Fresh packets are written to `.token-economy/checkpoints/` and kept under 2000 estimated tokens by default. Each packet includes:

- mandatory plan-mode instruction
- goal and current plan
- memory pointers
- touched files, commands, and errors extracted from transcript when provided
- open decisions and retrieval instructions

## Commands

```bash
./te context status
./te context checkpoint --goal "..." --plan "..." --transcript /path/to/transcript.jsonl
./te context fresh-start
```
