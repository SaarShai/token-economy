---
schema_version: 2
title: Prefix Caching
type: concept
domain: framework
tier: semantic
confidence: 0.65
created: 2026-04-25
updated: 2026-04-25
verified: 2026-04-25
sources: [raw/2026-04-17-research-brief.md, raw/m5-outputs-2026-04-18/P5_anthropic_cache_best_practices.md]
supersedes: []
superseded-by:
tags: [prompt-caching, cost]
---

# Prefix Caching

Prompt caching rewards stable prefixes. Put stable instructions, schemas, examples, and reference material before volatile user/task content. Avoid rewriting always-loaded files unless the cache win is worth invalidation.

Related: [[raw/2026-04-17-research-brief]]
