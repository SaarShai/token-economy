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

Provider effort:
- Claude: low/medium/high thinking budget.
- OpenAI: `reasoning.effort` low/medium/high.
- Gemini: `thinking_config.thinking_budget`.
- Local: compact prompt, bounded exploration.

Rule: orchestrator keeps final synthesis.

