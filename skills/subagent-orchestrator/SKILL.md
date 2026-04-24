---
name: subagent-orchestrator
description: Route work to cheaper or specialist subagents while keeping final synthesis local.
---

# Subagent Orchestrator

Trigger: task has >3 steps, research, codegen, review, or independent subtasks.

Protocol:
1. `./te delegate plan "<task>"`.
2. Send subagent minimal context: task, refs, budget, expected output.
3. Require sources + confidence.
4. Run independent subtasks in parallel when scopes do not overlap.
5. Reject reports that miss contract.
6. Orchestrator keeps final synthesis and final plan authorship.
7. Use any available model family the host provides; do not hardcode Claude/OpenAI/Gemini names into the workflow.

Never:
- send full transcript
- use reasoning_top for simple extraction
- delegate final synthesis
