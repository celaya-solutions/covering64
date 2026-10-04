```text
Document:    Combined Template-Hull and Hub-Count Priority Results
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      f1ea459fb601be3cdfdbb6de3bd269cfcbf78ce32b819f90979a28e10214f152
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Priority screen results

All 23 combined template-hull/hub-count models finished. There were 22
numerical OPTIMAL results and one positive certificate, with no unknowns or
timeouts. The total solver time was 164.568148 seconds; the longest
representative used 14.687233 seconds, within the 15-second budget.
No saved primal was a near-integral block selection.

`matching-032` is excluded in its remaining hub case `(m4,z)=(0,1)`. The
independent checker verified the exact positive gap `7651/1000000`, all 4,550
unchanged original hull rows, exactly two independently reconstructed hub
rows, all seven fixed block rows, and all 61,576 unit-box variables. Eight
damaged controls were rejected. It then joined this certificate with the five
previously checked hub cases, covering the exhaustive six-case partition.

The checked union is now **106 excluded first-link types and 152 open** out of
the original 258. This is a restricted regular-branch result, not an
unrestricted covering-number lower bound. The other 22 priority cases remain
open; their numerical LP solutions are not exact feasible witnesses or covers.

The saved-record checker verified all 23 records and all 22 primals. It
reconstructed the two hub equalities, checked unchanged original rows, fixed
and reset states, hashes, and remaining solver budgets. Exact arithmetic on
the stored binary values found a maximum numerical row residual of about
`2.314e-12`. Cycle primals had 379–408 fractional blocks; matching survivors
had 388–410.

## Evidence

- Run: `experiments/scratch/four-seven-template-hub-priority-20261003`.
- Raw results SHA-256: `40bb25f15d34efb8a2d968d269f637fb6d29c61b868bfb86113ef086d1667986`.
- Readback audit SHA-256: `ab2165a38cd0336cf9f88d990e7d441e489f63bc2b1315a418245b8158a82337`.
- Independent replay and six-case join: `../four-seven-template-hub-independent/matching-032-audit.json`.
- Independent audit SHA-256: `9037e9529d648e391104cfe81f08e52ef784c1b5511230f2e5eca6541c294478`.
- Preserved 106-ID union: `../four-seven-template-hub-independent/combined-first-link-exclusions.json`.
- Union SHA-256: `dc1f0790d593238d00c8eff3ac58753d70a7fc9c6820d73d0bb835569ac9fd0e`.

The raw solver record keeps its original pending flag. The separate independent
audit and this report record its later verification. Frozen original matrices,
catalogs, and previous campaign evidence were not changed. No external source
was needed for this finite model-combination experiment.
