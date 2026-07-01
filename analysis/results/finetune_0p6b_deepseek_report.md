# Committed — eval report

- Examples judged: **442**  |  candidate model: `deepseek`

## Deployment estimate (headline — reweighted to true test distribution)
- Prefix-type accuracy: **0.601**  (always-`fix` floor: **0.489**)
- Conjunctive pass-rate: **0.359**  |  graded mean (0–3): 2.094

## Deterministic (sample, equal-allocation — diagnostic)
- BLEU: 8.42  (short-text caveat — not a headline)
- ROUGE-L (F): 0.278
- Prefix-type accuracy (sample): 0.419  (always-`fix` floor: 0.113)

## LLM judge — composite (gate-then-grade)
- Conjunctive pass-rate (all four axes pass): **0.326**
- Graded mean (0–3, type-gated=False): 1.962

### Per-axis vector
- type_correctness: fail=0.27, pass=0.73
- faithfulness: fail=0.19, pass=0.81
- completeness: fail=0.27, pass=0.73
- specificity: fail=0.45, pass=0.55
