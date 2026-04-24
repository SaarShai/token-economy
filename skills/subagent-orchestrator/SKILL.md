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
8. If the task repo has a GitHub remote, route save-points to a lightweight repo-maintainer worker using `prompts/subagents/repo-maintainer.prompt.md`.
9. Manage worker lifecycle with `prompts/subagents/lifecycle.prompt.md`: capture result, document/feed it forward, then close completed idle workers.

Never:
- send full transcript
- use reasoning_top for simple extraction
- delegate final synthesis
- run repo maintenance when no GitHub remote exists
- close active workers just to free thread capacity
