---
type: project
axis: skill_crystallization
tags: [skill, L3-sop, automation]
confidence: low
evidence_count: 0
---

# skill-crystallizer — auto-convert solved tasks → reusable L3 SOPs

**Status: SPEC / SKELETON.** Detects completed tasks in a Claude Code session and writes them as L3 SOPs (context-keeper-v2 tier).

## When a task is "solved"

Heuristic signals (need ≥2 to fire):
1. User ended with positive close: "done", "works", "ship it", "good", ✓.
2. Final tool call was a successful test/verify/build.
3. Recent git commit with non-trivial diff.
4. No open TodoWrite items flagged incomplete.
5. `verify` or `test` tool returned grounded=true within last 5 turns.

## Extraction

1. Walk transcript backwards from close-signal to find task-start.
2. Extract: user goal (first imperative), tool sequence, files touched, key decisions, failed attempts avoided.
3. Pass to LLM (local gemma/qwen or Anthropic Haiku) → structured SOP markdown.
4. Save via `tier_manager.record_task_completion(slug, steps, outcome)`.

## Hook

`SessionEnd` hook runs the detector. Slow OK (seconds not milliseconds).

## Non-goals

- Not extracting general knowledge — that's L2 facts.
- Not creating SOPs for trivial one-tool tasks.
- Not overwriting existing SOPs (manual merge if pattern repeats).

## Not implemented yet
- `detector.py` — finds solved-task windows in transcript.
- `extractor.py` — LLM-based structured extraction.
- `hook.sh` — SessionEnd entry.

## Borrowed from

- GenericAgent: `update_working_checkpoint` + `start_long_term_update` pattern.
- Our context-keeper v1: transcript parsing utilities (reused).
