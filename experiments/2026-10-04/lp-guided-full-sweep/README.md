```text
Document:    Complete Single Neighborhood LP Sweep
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      12f67214e3ca24394e9a3032a8fc54ad2c69fe0390d8a41408442e4b700e022d
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Complete single-neighborhood sweep

All 136 valid two-edge-switch neighbors of the selected heavy pattern were
accounted for: 23 exact-input-matching cached OPTIMAL results and 113 fresh LP
solves. All 136 reported numerical OPTIMAL. Fresh solver time was
16.920772911282256 seconds; the run used 18.545826375018805 wall seconds.

The starting elastic objective was 5.575882992498541. The best neighbor's objective
was 5.644705064246714, so every neighbor was numerically worse. No improving tuple,
checked fractional completion, or covering witness was found. This is a complete
numerical no-improvement result for this one two-edge-switch neighborhood in the
fixed regular four-sevenfold family. It is not an unrestricted lower bound, an
exact local-optimality theorem, or evidence excluding larger moves.

The planned multi-round continuation required an improvement in this sweep.
That condition was not met, so no continuation or second neighborhood was run.

## Preparation and validation

The frozen generator and independently audited 697-row/1,200-ordinary-variable
LP basis are reused unchanged from the bounded pilot. The full neighborhood
was fixed before the run and matched the previous pilot's final 136-candidate
ranking exactly. The initial 14-cut bundle determined evaluation order; the
newly derived fifteenth cut was not added during this frozen run.

Preparation matched cached heavy IDs, affine row hashes, source ranking hashes,
numerical vector hashes and numerical OPTIMAL status. The focused independent
gate in `../lp-guided-complete-sweep-independent/` re-enumerated all 136 candidates,
checked all 94,792 affine row shifts and all 23 cache bindings and residuals,
and reviewed the solver source delta. The only solver change from the bounded
pilot is capture of its 697-row numerical dual vector alongside each 1,200-entry
numerical primal vector. A fresh GLOP instance is still used per LP.

Limits were one neighborhood, one worker, one second per LP, 40 accumulated
solver seconds and 60 wall seconds. The runner checks a 1.1-second margin before
starting a new LP. It saves vectors and record hashes and directly recomputes
each elastic residual. A near-zero residual triggers exact rational feasibility
checking and would stop this run. No such candidate occurred.

`stitch.py` separately checks a family formed by each accepted improving heavy
tuple plus the original 36 ordinary blocks, using both cover verifiers. There
were zero accepted improvements here, so `stitched/checks.json` reports zero
new stitched candidates. The pre-existing five-hole partial belongs to the
separate `../lp-guided-best-lp/` diagnostic and was not rediscovered by this sweep.

## Artifacts

`proposal.json` binds the complete neighbor list, cache records, source/model
hashes and budgets. `result.json` records all 136 outcomes. Every fresh primal
and dual vector, plus frozen input snapshots, start metadata and all evaluations,
is saved under ignored `experiments/scratch/lp-guided-full-sweep-20261004/`.
Independent post-run readback is maintained by the reviewer in the focused gate
folder. This sweep was run once. No optimizer call was made during preparation.

- `sweep.py` SHA256: `282b4d2844547aeaae3963b6bc8b7efc5448a1d839fd8e56d39d1e4e22626a69`
- `proposal.json` SHA256: `b7b7bb00458def12a45b661105283703e6ace1861bcc24dda173b9b0295b4b8d`
- `result.json` SHA256: `894dde1989854eac39dec71b676c91a6b09e3c98f28fa2feb47b6898214c888c`
- `stitch.py` SHA256: `10a03e6c80dc4df1691bef6a4387049ae92890ecafdc9be2ed650568e6433613`
- `stitched/checks.json` SHA256: `7c1c41173413a54844b46512e0eadc033ce1822525aa5593025961baef039c4f`
