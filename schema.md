# Token Economy Wiki — Schema

Purpose: persistent knowledge base for building tools that reduce LLM token/compute consumption. Karpathy 3-layer (raw/wiki/schema) + obsidian-mind hooks + git-wiki immutability.

## Folders
- `raw/` immutable sources (papers, repos, gists). Filename: `YYYY-MM-DD-slug.md`.
- `concepts/` atomic ideas (one technique per page).
- `patterns/` reusable workflows, recipes.
- `projects/` active builds (our tools).
- `people/` humans (authors, collaborators).
- `queries/` durable Q&A.

## Frontmatter
```
---
type: concept|pattern|project|person|raw|query
tags: [token-compression, caching, ...]
confidence: low|med|high
evidence_count: N
related: [[page]]
---
```

## Ops
- **Ingest**: new source → `raw/`, update ≥3 concepts, append `log.md`, update `index.md`.
- **New concept**: full frontmatter, link related, add to index.
- **Evidence up**: bump `evidence_count`, recalibrate confidence.
- **Contradiction**: flag both pages, downgrade confidence, log.

## Confidence rungs
- low: 1 source, unverified
- med: 2+ sources OR 1 source + sanity check
- high: 3+ sources + independent verification + measured numbers
