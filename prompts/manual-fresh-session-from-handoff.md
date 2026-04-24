# Manual fresh session from handoff

Copy-paste this into the fresh/new session after `session_handoff.md` has been created.

```text
Read only `start.md` and `session_handoff.md` from the repo root containing `token-economy.yaml`.

Follow `start.md` exactly:
- run `./te doctor`
- read `token-economy.yaml`
- load `L0_rules.md` and `L1_index.md` only through the normal startup path
- use progressive retrieval only when needed

Use `session_handoff.md` as the sole continuity packet. Load into context only:
- the current task
- what is done
- what is in progress or blocked
- next steps
- touched paths needed for the next step
- exact commands/errors/decisions needed to avoid repeating mistakes
- wiki/documentation references to retrieve later if relevant

Do not inline or fetch linked wiki pages unless the next action actually needs them. When retrieval is needed, search or fetch the narrowest relevant page using:
`./te wiki search "<query>"`
`./te wiki timeline "<id>"`
`./te wiki fetch "<id>"`

Start in plan mode. Think step by step. First produce a compact implementation plan grounded only in `start.md`, `session_handoff.md`, and any narrowly retrieved references. Do not execute until the plan is clear.
```
