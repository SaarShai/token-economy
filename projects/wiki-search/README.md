---
type: project
axis: knowledge_org
tags: [retrieval, progressive-disclosure, mcp, wiki]
confidence: med
evidence_count: 0
---

# wiki-search — progressive-disclosure retrieval over the Token Economy wiki

**Status: SPEC / SKELETON.** Adopts claude-mem's 3-layer retrieval pattern (index → timeline → fetch) for any Obsidian-style markdown wiki.

## Problem

Our wiki is 70+ markdown files, ~400KB. Loading whole pages into context is wasteful. Grep alone returns fragments without structure. Need tiered retrieval that exposes the minimum necessary.

## 3-layer API (MCP tools)

```
wiki_search(query, k=10)    → tier-1: IDs + one-line previews (~50-100 tok each)
wiki_timeline(id, window=3) → tier-2: neighbor pages + backlinks
wiki_fetch(id)              → tier-3: full page content
```

Agent uses tier-1 → evaluates relevance → tier-2 or tier-3 only on hits.

## Implementation plan

1. `index.py` — builds inverted index + FTS5 SQLite over wiki/*.md.
2. `retriever.py` — 3-layer search with BM25 + optional embedding rerank.
3. `mcp_server.py` — exposes wiki_search/wiki_timeline/wiki_fetch.
4. Hook: SessionStart injects L1-style summary `{ index path: N pages, M concepts, K projects }`.

## Stores

- SQLite at `~/.cache/wiki-search/<vault>/index.db`.
- Rebuilds on file modification (watchdog).
- Optionally vector index via sentence-transformers (opt-in, heavier).

## Not implemented yet

This doc. Implementation follows context-keeper-v2 + write-gate (share MCP scaffold).

## Borrowed

- **claude-mem**: 3-layer retrieval + ID-based citations.
- **GenericAgent**: L1 pointer-index discipline.
- **Karpathy wiki**: index.md as canonical catalog.
