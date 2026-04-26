---
name: wiki-write
description: Create or update durable wiki memory after verified work.
---

# Wiki Write

Trigger:
- verified finding
- user-confirmed decision
- source ingested
- reusable procedure discovered
- non-trivial failure lesson worth preventing later

Protocol:
1. Search existing pages first.
2. Prefer updating a matching page over creating a new one; fewer rich pages beat many thin one-off pages.
3. If no page, run `./te wiki new --template page --title "<title>" --domain "<domain>"`.
4. Name new pages at domain/category level, not task-specific bug names.
5. Fill v2 frontmatter completely.
6. For procedures/failures, include when it applies and the exact prevention rule.
7. Add >=2 useful wikilinks when possible.
8. Append `log.md`.
9. Run `./te wiki index`; for new v2 pages run `./te wiki lint --strict`.

Never:
- write durable memory from unexecuted plans
- inflate trivial lookups/status checks into fake procedures
- mutate `raw/` after creation
- create duplicate page without supersession
