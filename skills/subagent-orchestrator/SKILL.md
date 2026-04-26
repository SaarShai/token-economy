---
name: subagent-orchestrator
description: Route work to cheaper or specialist subagents while keeping final synthesis local.
---

# Subagent Orchestrator

Trigger: task has >3 steps, research, codegen, review, or independent subtasks.

Protocol:
1. `./te delegate plan "<task>"`.
2. Delegate only when saved main-context/tool cost exceeds orchestration overhead.
3. Send subagent minimal context: task, refs, budget, expected output.
4. Require compact packet: outcome, sources, confidence, verification, changed files, risks.
5. Run independent subtasks in parallel only when their outputs are distinct and the merge step stays small.
6. Reject reports that miss contract.
7. Orchestrator keeps final synthesis and final plan authorship.
8. Use any available model family the host provides; do not hardcode Claude/OpenAI/Gemini names into the workflow.
9. If the task repo has a GitHub remote, route save-points to a lightweight repo-maintainer worker using `prompts/subagents/repo-maintainer.prompt.md`.
10. Manage worker lifecycle with `prompts/subagents/lifecycle.prompt.md`: capture result, document/feed it forward, then close completed idle workers.

Result budget:
- summary <= 1500 tokens unless user explicitly requests detail
- no transcripts or raw logs unless needed as evidence
- include URLs/paths instead of pasted source when possible

Never:
- send full transcript
- use reasoning_top for simple extraction
- delegate final synthesis
- run repo maintenance when no GitHub remote exists
- close active workers just to free thread capacity
