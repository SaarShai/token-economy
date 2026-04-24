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

Protocol:
1. Search existing pages first.
2. If no page, run `./te wiki new --template page --title "<title>" --domain "<domain>"`.
3. Fill v2 frontmatter completely.
4. Add >=2 useful wikilinks when possible.
5. Append `log.md`.
6. Run `./te wiki index`; for new v2 pages run `./te wiki lint --strict`.

Never:
- write durable memory from unexecuted plans
- mutate `raw/` after creation
- create duplicate page without supersession

