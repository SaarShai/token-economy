# Summarize For Handoff

Use cheapest capable summarizer. This is for fresh context only, not durable wiki documentation.
Send durable-but-not-needed findings to `prompts/subagents/wiki-documenter.prompt.md` and link to resulting wiki pages instead of loading them.
If the user appended future work after `summ`, include it as next-session requirements; do not execute it or expand it here.

Output only this structure:

```markdown
---
type: handoff
from-session: <id>
created: <ISO-8601>
context-pct-at-refresh: <n>
next-mode: plan-first
---

# HANDOFF - <task-slug>

## 1. Current task (1-liner)
## 2. What done
## 3. What in-progress (blockers)
## 4. What next (priority order)
## 5. Key files touched (paths only - do NOT re-read speculatively)
## 6. Key decisions + reasoning (why, not what)
## 7. Wiki pages updated / created (wikilinks)
## 8. Open questions
## 9. Instructions for next agent
- Start in plan mode. Think step-by-step.
- Read this handoff + `start.md` only. Do not load full wiki.
- Build plan before executing.
- On complete: update wiki, log entry, create fresh handoff if context > 20%.
- If this packet was emitted because the old host could not clear context, continue only in the fresh session.
```

Keep <=2000 estimated tokens. Preserve exact errors and paths. Exclude transcript noise, raw logs, broad wiki pages, docs-only discoveries, and detailed plans that should be made after the refresh.
