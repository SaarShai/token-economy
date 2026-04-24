# Token Economy Adapter

Read `start.md` first. Keep this file tiny.

- Default style: Caveman Ultra.
- On session start: run `./te doctor` if available, then load only `L0_rules.md` and `L1_index.md`.
- Retrieve wiki facts with `./te wiki search`, then `timeline`, then `fetch`.
- At 20% context used: `./te context checkpoint`; prefer fresh session with `./te context fresh-start`.
- Use ComCom, semdiff, context-keeper, and delegate-router when available.
- Do not load raw sources, old sessions, or full wiki pages unless relevant.

