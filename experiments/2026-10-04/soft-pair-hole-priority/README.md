```
Document:    Hole-Priority Soft-Pair Model Preparation
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      da65e29208c7095bfe7057e197655a787c255567db61caf88ddc758053f5a8f2
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Hole-priority soft-pair preparation

Status: prepared for the root's independent gate. No optimizer has been called.

This model keeps every constraint, variable domain, variable name, and four named core caps from the preceding soft H12 model. The full serialized models match after clearing only their hints and objectives. The new complete hint uses the durable final-family copy in `soft-pair-h12-relabel-novelty`, SHA256 `cadb86e4f2243eada269dc314bca0bc5c238f5b0ca2bd9525dd0b67aad24c970`. Its raw source hash is also bound. Counts, holes, and canonical deficits were derived independently by direct containment and checked against the separate subset recount and frozen diagnostic.

The objective is `15361*holes + sum(d_P)`. There are 120 deficit variables, each in `[0,128]`, so their total is between 0 and 15,360. Reducing holes by one lowers the objective by at least 15,361, more than any possible increase in the deficit total. Thus holes have exact lexicographic priority; deficits break ties. This proof concerns the unchanged declared variable domains, including any valid auxiliary slack.

| Prepared setting | Value |
|---|---:|
| Time limit | 300 seconds |
| Workers | 4 |
| Seed | 2026105001 |
| Initial holes | 12 |
| Initial actual D2max / D2sum | 32 / 32 |
| Initial D3 / D4 | 0 / 0 |
| Initial minimum pair count | 5 |
| Four named core overlaps | 1, 1, 1, 2 |
| Canonical and solver hint objective | 15361 * 12 + 32 = 184,364 |
| Complete hint entries / rows checked | 5,728 / 14,405 |

Only the seed changes in the solver parameters; the preceding run already used 300 seconds and four workers. The hint is guidance and does not fix any block choice. No additional constraints or symmetry assumptions are introduced.

The runner keeps every callback and feasible final full vector, canonical vector, row check, actual recount, witness, dual-verifier result, and log. Its solver-objective check uses the new coefficients; its canonical objective is `15361*actual holes + actual D2max`. It allows solver deficit slack and never confuses that slack with actual defects.

The sole early-stop condition is an actual cover with zero holes and matching successful package and standalone verifier verdicts. A positive-hole family with actual D2max = D2sum = D3 = D4 = 0 and passing pair, core, and profile checks is recorded separately as `qualified_D2zero_hint`; it does not trigger a stop. Pure classification and arithmetic controls passed, including deliberate inconsistent verifier verdicts and the actual H12/D2=32 input. Synthetic cover and zero-hint classification controls are not covering families or feasible zero-deficit witnesses.

`manifest.json` binds all source and input hashes, the prior gate and model, the tracked and raw candidate, the full hint, parameter file, and semantic-control receipt. Full models and vectors remain in ignored scratch. The root must independently gate and launch the sole experiment. UNKNOWN or a time limit is inconclusive, and no global lower-bound claim is made.
