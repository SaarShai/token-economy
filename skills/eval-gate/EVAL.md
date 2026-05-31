# EVAL — `eval-gate`

LLM-as-judge quality gate. **Status: opt-in, unmeasured** — plumbing verified
offline; effectiveness A/B pending (N≥50 before any default promotion).

## Verified — plumbing (offline, no network)

`bash skills/eval-gate/tools/test.sh` — exercises all three verbs via
`--stub-score` (deterministic, no model):

- `score` pass (stub 5 → 1.0 ≥ 0.7) → exit 0
- `score` fail (stub 2 → 0.4 < 0.7) → exit 1
- `score` empty candidate → exit 2
- `add-case` rejects a thin reason and a reasonless ("no why") reason → exit 1
- `add-case` accepts a why-bearing reason, appends exactly one JSONL line → exit 0
- `add-case --force` overrides the gate → exit 0
- `suite` all-pass → exit 0; any case below threshold → exit 1
- `suite` mean-regression vs a saved baseline → exit 1
- judge-unreachable / unparseable → exit 2 (gate fails safe, never ships blind)

## Pending — effectiveness A/B

The claim to test is *not* token savings (this skill spends tokens to buy
quality); it's **defect catch-rate vs false-reject**:

| Metric | Without eval-gate | With | Target |
|---|---|---|---|
| bad outputs shipped (escapes) | | | ↓ |
| good outputs wrongly blocked (false rejects) | | | ≈0 |
| judge–human score agreement | | | ≥0.8 corr |

Protocol: build a 50-case set (25 known-good, 25 known-bad) for one real task;
score each; compare the gate's pass/fail to human labels. Judge: Ollama local
(smoke) → MiMo (production). The rubric is the variable — measure how rubric
specificity moves agreement.

## Failure modes

- Rubric too vague → low judge–human agreement (the score is noise). Mitigation:
  specificity; the agreement metric above surfaces it.
- Judge model too small → inconsistent scores. Use a 7B+ instruct model or MiMo.
- Self-judging (same model generates + judges) can run lenient; temp 0 + an
  external rubric mitigate but don't eliminate.

## Lineage / sources

- `eval/judge.py` — backends + 0-5 scoring lifted here.
- LLM-as-judge + regression-suite + failure→case ratchet (the standard ML-eng
  eval loop), applied to agent / content output.
