---
name: wiki-retrieve
description: Retrieve all and only relevant LLM wiki information.
---

# Wiki Retrieve

Use when task references past work, decisions, docs, memory, "have we done X", or project facts.

Protocol:
1. Read `L1_index.md`.
2. Run `./te wiki search "<query>"`.
3. For relevant hits, run `./te wiki timeline "<id>"`.
4. Fetch at most 3 pages first with `./te wiki fetch "<id>"`.
5. If insufficient, fetch <=2 more pages.
6. Cite page paths/IDs.

Never:
- load whole vault
- fetch raw archive speculatively
- cite superseded page without noting newer page

