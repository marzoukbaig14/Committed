# Committed — eval report

- Examples judged: **442**  |  candidate model: `gemini`

## Deployment estimate (headline — reweighted to true test distribution)
- Prefix-type accuracy: **0.131**  (always-`fix` floor: **0.489**)
- Conjunctive pass-rate: **0.181**  |  graded mean (0–3): 1.207

## Deterministic (sample, equal-allocation — diagnostic)
- BLEU: 2.17  (short-text caveat — not a headline)
- ROUGE-L (F): 0.156
- Prefix-type accuracy (sample): 0.113  (always-`fix` floor: 0.113)

## LLM judge — composite (gate-then-grade)
- Conjunctive pass-rate (all four axes pass): **0.156**
- Graded mean (0–3, type-gated=False): 1.138

### Per-axis vector
- type_correctness: fail=0.67, pass=0.33
- faithfulness: fail=0.57, pass=0.43
- completeness: fail=0.48, pass=0.52
- specificity: fail=0.19, pass=0.81

## Judge-vs-human validation (n=50)
- type_correctness: raw_agreement=0.8, cohen_kappa=0.519
- faithfulness: raw_agreement=0.68, cohen_kappa=0.384
- completeness: raw_agreement=0.7, cohen_kappa=0.439
- specificity: raw_agreement=0.86, cohen_kappa=0.194
