# Personal Assistant Router

Use for prompts prefixed `/pa` or `/btw`: route small or context-light requests away from the expensive main model.

## Protocol

1. Do not load the full transcript, `start.md`, raw wiki pages, or repo files.
2. Run:
   ```bash
   ./te pa --directive "<prompt>"
   ```
3. Use the returned packet to select the cheapest capable handler and the smallest context bundle.
4. Escalate to the main/frontier model only when the packet says `escalate_to_main`, confidence is low, or the task is high-risk.
5. Ask the handler for the compact result contract only:
   - answer_or_outcome
   - sources_or_evidence
   - confidence
   - verification
   - risks
   - changed_files/tests/exact_errors for code tasks

## Context Rules

- Project facts: search `L1_index.md` or `te wiki search` before fetching notes.
- Files: load only mentioned paths or search hits.
- Web: use only when task asks for current/external facts or uncertainty requires it.
- Memory writes: only after verified execution; never store untested intentions.

## Style

Caveman Ultra. Preserve exact code, paths, numbers, math, and errors.
