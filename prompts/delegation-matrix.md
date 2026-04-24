# Delegation Matrix

| Task class | Primary | Fallback | Never |
|---|---|---|---|
| Planning / synthesis / review | reasoning_top | medium | lightweight |
| Complex coding | coding_top | reasoning_top | lightweight |
| Literature / summarization | lightweight | medium | reasoning_top |
| Fact extraction / grep | lightweight | local | reasoning_top |
| Adversarial review | reasoning_top | medium | lightweight |
| Math / proof | reasoning_top | local | lightweight |
| File reads / tool execution | medium | lightweight | reasoning_top |
| Repo save-point / commit / push | lightweight | medium | reasoning_top |

Provider effort:
- Claude: low/medium/high thinking budget.
- OpenAI: `reasoning.effort` low/medium/high.
- Gemini: `thinking_config.thinking_budget`.
- Local: compact prompt, bounded exploration.

Rule: orchestrator keeps final synthesis.
Model choice is capability-based and host-agnostic. The router should select from whatever cheap, medium, frontier, local, or high-context models are available in the registry.

`/pa` or `/btw` bypass:
- Run `te pa --directive "<prompt>"`.
- Route with no full transcript and no full wiki fetch by default.
- Personal-assistant router chooses the cheapest capable handler plus minimal context.
- Escalate back to main/frontier only for high-risk, ambiguous, architectural, destructive, or final-synthesis work.

GitHub repo maintenance:
- Activate only when `git remote -v` shows a GitHub remote for the task repo.
- Use `prompts/subagents/repo-maintainer.prompt.md`.
- Trigger after verified milestones, before context refresh/handoff, and when user asks to save progress.
- Stage only intended task files; never sweep unrelated changes.

Subagent lifecycle:
- Use `prompts/subagents/lifecycle.prompt.md` when supervising workers or when thread limits are near.
- Close only completed, failed, cancelled, or superseded workers after the result packet is read and useful output is documented or merged into the main plan.
- Keep a compact worker ledger in the task queue or handoff.
