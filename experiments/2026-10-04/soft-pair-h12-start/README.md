```
Document:    Soft Strong-Pair H12 Start Preparation
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      b9b6820ff76dd6029ca2064d2f899473c32a043b9153dd1953ef4cfccb7fd02f
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# H12-seeded soft-pair preparation

Status: prepared for an independent root gate. No optimizer has been called.

This experiment preserves the earlier `soft-strong-pair-four-core` model. The full serialized model, after clearing only its solution hint, is identical to that prior gated model. All 5,728 variable names and domains, all 14,405 constraint rows, the objective, variable order, and four named core caps are unchanged. The parameter comparison permits only the time limit to change from 120 to 300 seconds and the random seed from `2026104302` to `2026104901`; four workers and both logging settings remain unchanged.

The complete hint now uses the independently verified H12 family from native variable-cardinality seed `2026104702`. Its 64 block choices, 120 pair counts, 560 triple counts, 560 hole flags, and 120 canonical per-pair deficit variables were derived by direct block containment, then compared against the separate subset-based recount. The package and standalone verifiers agree on 12 uncovered triples. The frozen structural profile and both verifier receipts are bound by hash, as are the existing all-relabel certificate and prior model gate.

| Initial measure | Value |
|---|---:|
| Holes | 12 |
| D2max / D2sum | 34 / 34 |
| D3 / D4 | 0 / 0 |
| Minimum pair count | 5 |
| Four named core overlaps | 1, 1, 1, 2 |
| Complete hint objective | 561 * 34 + 12 = 19,086 |
| Hint entries | 5,728 |
| Constraint rows checked | 14,405 |
| Active constraint rows for this hint | 13,845 |

The hint is feasible for the unchanged soft model. It remains a noncover. The hint supplies guidance only; it fixes no block choices and adds no constraints.

The gated runner requires an explicit GO receipt bound to the new manifest, model, parameters, complete hint, and runner source. It verifies the frozen source and input hashes before the sole solve. Every callback and feasible final state retains its full solver vector, canonical vector, model-row check, actual deficit recount, witness, dual-verifier results, and logs. It accepts auxiliary deficit slack while rejecting deficits below their actual values. The prior actual-D2zero stopping rule is unchanged: stop only after a saved family has recounted D2max zero and passes the accompanying hard-row, core-cap, and global-profile checks. A D2zero noncover is a qualifying next-stage hint, not a covering witness.

Raw model, parameter, hint, and archived source artifacts remain under ignored scratch. `manifest.json` binds these artifacts and all prior inputs; `preparation.json` records the complete-hint validation. The root will independently gate and launch this experiment. UNKNOWN or a time limit is inconclusive, and this preparation supplies no global lower-bound claim.
