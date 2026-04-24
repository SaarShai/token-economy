---
type: project
axis: knowledge_org
tags: [retrieval, progressive-disclosure, mcp, wiki]
confidence: med
evidence_count: 0
---

# wiki-search — progressive-disclosure retrieval over the Token Economy wiki

**Status: IMPLEMENTED v1.** Adopts claude-mem's 3-layer retrieval pattern (index -> timeline -> fetch) for any repo-local markdown wiki.

## Problem

Our wiki is 70+ markdown files, ~400KB. Loading whole pages into context is wasteful. Grep alone returns fragments without structure. Need tiered retrieval that exposes the minimum necessary.

## 3-layer API (CLI + importable + optional MCP)

```
wiki_search(query, k=10)    → tier-1: IDs + one-line previews (~50-100 tok each)
wiki_timeline(id, window=3) → tier-2: neighbor pages + backlinks
wiki_fetch(id)              → tier-3: full page content
```

Agent uses tier-1 → evaluates relevance → tier-2 or tier-3 only on hits.

CLI:

```bash
./te wiki index
./te wiki search "context refresh"
./te wiki timeline projects/context-keeper-v2/README
./te wiki fetch projects/context-keeper-v2/README
```

Python:

```python
import sys
sys.path.insert(0, "projects/wiki-search")
from wiki_search import wiki_search, wiki_timeline, wiki_fetch
```

MCP:

```bash
python projects/wiki-search/mcp_server.py
```

## Implementation

- Core code: `token_economy/wiki.py`.
- Wrapper: `projects/wiki-search/wiki_search.py`.
- Optional MCP: `projects/wiki-search/mcp_server.py`.
- SQLite FTS5 index at `.token-economy/wiki.sqlite3`.
- L1 pointer index at `L1_index.md`.

## Stores

- SQLite at repo-local `.token-economy/wiki.sqlite3`.
- Rebuilds on file modification (watchdog).
- Optionally vector index via sentence-transformers (opt-in, heavier).

## Borrowed

- **claude-mem**: 3-layer retrieval + ID-based citations.
- **GenericAgent**: L1 pointer-index discipline.
- **Karpathy wiki**: index.md as canonical catalog.
