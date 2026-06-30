# Committed — eval report

- Examples judged: **442**  |  candidate model: `deepseek`

## Deployment estimate (headline — reweighted to true test distribution)
- Prefix-type accuracy: **0.154**  (always-`fix` floor: **0.489**)
- Conjunctive pass-rate: **0.101**  |  graded mean (0–3): 0.777

## Deterministic (sample, equal-allocation — diagnostic)
- BLEU: 0.86  (short-text caveat — not a headline)
- ROUGE-L (F): 0.121
- Prefix-type accuracy (sample): 0.118  (always-`fix` floor: 0.113)

## LLM judge — composite (gate-then-grade)
- Conjunctive pass-rate (all four axes pass): **0.086**
- Graded mean (0–3, type-gated=False): 0.672

### Per-axis vector
- type_correctness: fail=0.70, pass=0.30
- faithfulness: fail=0.71, pass=0.29
- completeness: fail=0.65, pass=0.35
- specificity: fail=0.59, pass=0.41
