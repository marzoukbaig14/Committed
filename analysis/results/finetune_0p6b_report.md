# Committed — eval report

- Examples judged: **442**  |  candidate model: `gemini`

## Deployment estimate (headline — reweighted to true test distribution)
- Prefix-type accuracy: **0.601**  (always-`fix` floor: **0.489**)
- Conjunctive pass-rate: **0.321**  |  graded mean (0–3): 1.810

## Deterministic (sample, equal-allocation — diagnostic)
- BLEU: 8.42  (short-text caveat — not a headline)
- ROUGE-L (F): 0.278
- Prefix-type accuracy (sample): 0.419  (always-`fix` floor: 0.113)

## LLM judge — composite (gate-then-grade)
- Conjunctive pass-rate (all four axes pass): **0.308**
- Graded mean (0–3, type-gated=False): 1.821

### Per-axis vector
- type_correctness: fail=0.20, pass=0.80
- faithfulness: fail=0.22, pass=0.78
- completeness: fail=0.31, pass=0.69
- specificity: fail=0.44, pass=0.56
