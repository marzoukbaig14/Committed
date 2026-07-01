# Committed — eval report

- Examples judged: **442**  |  candidate model: `deepseek`

## Deployment estimate (headline — reweighted to true test distribution)
- Prefix-type accuracy: **0.131**  (always-`fix` floor: **0.489**)
- Conjunctive pass-rate: **0.175**  |  graded mean (0–3): 1.447

## Deterministic (sample, equal-allocation — diagnostic)
- BLEU: 2.17  (short-text caveat — not a headline)
- ROUGE-L (F): 0.156
- Prefix-type accuracy (sample): 0.113  (always-`fix` floor: 0.113)

## LLM judge — composite (gate-then-grade)
- Conjunctive pass-rate (all four axes pass): **0.186**
- Graded mean (0–3, type-gated=False): 1.317

### Per-axis vector
- type_correctness: fail=0.70, pass=0.30
- faithfulness: fail=0.51, pass=0.49
- completeness: fail=0.46, pass=0.54
- specificity: fail=0.19, pass=0.81

## Judge-vs-human validation (n=50)
- type_correctness: raw_agreement=0.82, cohen_kappa=0.606
- faithfulness: raw_agreement=0.78, cohen_kappa=0.563
- completeness: raw_agreement=0.8, cohen_kappa=0.6
- specificity: raw_agreement=0.88, cohen_kappa=0.336
