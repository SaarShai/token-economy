# Subagent Lifecycle

Use when supervising spawned workers or when the host reports a thread/subagent limit.

## Close Rule

Close a subagent only when all are true:

1. Its task is complete, failed, cancelled, or superseded.
2. Its final result packet has been read by the orchestrator.
3. Useful results have been fed into the main plan, handoff, or final synthesis.
4. Durable findings have been written to the repo-local wiki/log or explicitly marked non-durable.
5. Open questions, errors, and follow-up tasks have been captured in the task queue or handoff.

Never close an active worker just to free capacity. If a worker is idle but has not returned a result, ask for status or cancel/supersede it explicitly before closing.

## Procedure

1. Poll worker status.
2. For completed workers, read the compact result packet.
3. Verify it satisfies the original contract: scope, sources, confidence, changed paths, commands, errors, and remaining risks.
4. Document durable results with `prompts/subagents/wiki-documenter.prompt.md` when needed.
5. Merge actionable results into the orchestrator's queue/plan.
6. Close the worker thread and record its id, task, result path/wiki link, and close reason.

## If Thread Limit Is Hit

1. Close completed documented workers first.
2. Then close failed/cancelled/superseded workers after capturing failure reason.
3. Do not spawn new workers until there is an available slot.
4. Prefer batching tiny follow-up tasks into one lightweight worker brief.

## Result Ledger

Keep a compact ledger in the active handoff or task queue:

```markdown
| worker | task | status | result captured | wiki/log | close reason |
|---|---|---|---|---|---|
```
