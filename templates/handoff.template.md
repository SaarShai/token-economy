---
schema_version: 2
title: "{{task_slug}}"
type: handoff
domain: framework
tier: working
confidence: 0.7
from-session: "{{session_id}}"
created: "{{date}}"
updated: "{{date}}"
verified: "{{date}}"
sources: []
supersedes: []
superseded-by:
tags: [handoff, context-refresh]
context-pct-at-refresh: "{{context_pct}}"
next-mode: plan-first
---

# HANDOFF - {{task_slug}}

## 1. Current task (1-liner)

{{goal}}

## 2. What done

- {{done}}

## 3. What in-progress (blockers)

- {{in_progress}}

## 4. What next (priority order)

- {{next}}

## 5. Key files touched (paths only - do NOT re-read speculatively)

- {{files_touched}}

## 6. Key decisions + reasoning (why, not what)

- {{decisions}}

## 7. Wiki pages updated / created (wikilinks)

- {{wiki_pages}}

## 8. Open questions

- {{open_questions}}

## 9. Instructions for next agent

- Start in plan mode. Think step-by-step. Create a robust plan before executing.
- Read this handoff + `start.md` only. Do not load full wiki.
- Build plan. Get user approval if host process requires approval. Then execute.
- On complete: update wiki, log entry, create fresh handoff if context > 20%.
