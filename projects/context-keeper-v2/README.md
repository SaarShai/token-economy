---
type: project
axis: cross_session_memory
tags: [context-keeper, v2, L0-L4, spec]
confidence: low
evidence_count: 0
---

# context-keeper v2 — L0-L4 tiered memory

**Status: SPEC / SKELETON.** v1 extracts intra-session state pre-compact. v2 adds true cross-session persistence + tiered retrieval, borrowed from GenericAgent.

## Tier schema

| tier | content | size | update cadence |
|---|---|---|---|
| **L0** meta-rules | behavioral axioms, CLAUDE.md-like invariants | ≤500 tok | rare, manual |
| **L1** index | pointer table: `keyword → file|line` | ≤1K tok, ≤30 lines | every session end |
| **L2** facts | paths, credentials, constants, env-specific | ≤3K tok | on verified action |
| **L3** SOPs | solved-task playbooks (one file per pattern) | 100-500 lines each | on task success |
| **L4** archive | compressed raw session transcripts | unlimited, cold | nightly cron |

## Files

```
~/.claude/memory/
├── L0_rules.md
├── L1_index.md
├── L2_facts/
│   ├── paths.md
│   ├── env.md
│   └── tool_configs.md
├── L3_sops/
│   ├── <task-slug>.md
│   └── ...
└── L4_archive/
    └── YYYY-MM/<session-id>.md.gz
```

## Write gate (see [[projects/write-gate/README]])

"**No execution, no memory.**" Only extractions from successful tool calls write to L2/L3. Plans or rationales without executed evidence stay in L4 archive.

## Session lifecycle

1. **SessionStart**: inject L0 + L1 into context. Full file load avoided — L1 points at what to load.
2. **Turn**: agent reads specific L2/L3 file via MCP on demand.
3. **Tool use**: `write_gate` evaluates, maybe promotes to L2 fact.
4. **Task completion**: skill-crystallizer writes L3 SOP.
5. **PreCompact**: context-keeper v1 runs (intra-session scratch) + appends to L4.
6. **Stop**: L1 index rebuilt from new L2/L3 files.

## Retrieval contract (MCP tool)

```
ck_query(keyword) → L1 hits (≤10 pointers)
ck_fetch(tier, slug) → full content of one L2/L3 file
ck_recent(days=7) → recent L4 archive entries
```

## Not implemented yet (this doc = spec)

- `tier_manager.py` — write-gate enforcement + tier promotion
- `l1_indexer.py` — rebuilds L1 from L2/L3 on demand
- `mcp_server.py` — exposes ck_query/ck_fetch/ck_recent

## Implementation plan

1. Convert current `~/.claude/memory/sessions/*.md` to L4 archive.
2. Write `tier_manager.py` with write-gate + promotion rules.
3. Write `l1_indexer.py`.
4. Wire into existing context-keeper PreCompact hook.
5. Build MCP server; register in Claude Code.
6. Eval: synthetic compaction fact-retention with/without v2.

## Caveats
- Not measured yet.
- MCP retrieval latency must stay <200ms.
- L1 rebuild must be incremental (not full scan) as L2/L3 grow.
