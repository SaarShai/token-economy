# Summarize For Handoff

Use cheapest capable summarizer. Output only this structure:

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
- Enter plan-mode. Think step-by-step.
- Read this handoff + `start.md` only. Do not load full wiki.
- Build plan before executing.
- On complete: update wiki, log entry, create fresh handoff if context > 20%.
```

Keep <=2000 estimated tokens. Preserve exact errors and paths.

