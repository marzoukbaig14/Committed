# Committed — eval report

- Examples judged: **442**  |  candidate model: `gemini`

## Deployment estimate (headline — reweighted to true test distribution)
- Prefix-type accuracy: **0.637**  (always-`fix` floor: **0.489**)
- Conjunctive pass-rate: **0.471**  |  graded mean (0–3): 2.188

## Deterministic (sample, equal-allocation — diagnostic)
- BLEU: 11.79  (short-text caveat — not a headline)
- ROUGE-L (F): 0.305
- Prefix-type accuracy (sample): 0.452  (always-`fix` floor: 0.113)

## LLM judge — composite (gate-then-grade)
- Conjunctive pass-rate (all four axes pass): **0.430**
- Graded mean (0–3, type-gated=False): 2.163

### Per-axis vector
- type_correctness: fail=0.19, pass=0.81
- faithfulness: fail=0.14, pass=0.86
- completeness: fail=0.27, pass=0.73
- specificity: fail=0.29, pass=0.71
