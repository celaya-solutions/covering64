```text
Document:    Independent Maximum Margin Pilot Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      48060ff7b44c2ea3775c69e56b43bbbc8c1b80d9cdfcfc6456caaa59a5e84ab3
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

The gate independently reconstructed the 277-variable integer model, including
605 structural rows and 333 normalized margin rows. It checked exact protobuf
equality, all source and input hashes, the nonnegative integer margin domain,
the maximum-margin objective, its safe upper bound 141507155, and the authorized
20-candidate, 3-second master, 1-second LP, 80-solver-second, 100-wall-second
budget. Three damaged controls were rejected. The gate did not invoke a solver.

The pilot completed 20 candidates in 62.475778 solver seconds and 65.539733 wall
seconds. All master responses were FEASIBLE, so the achieved margins are valid
but are not proved optimal. Every candidate had a positive exact separation
certificate. The cut collection grew from 333 to 353 independently checked
planes. Each new signed row weight has absolute value at most its denominator
1,000,000, so its normalized plane remains a valid elastic L1 lower bound.

The postchecker independently rebuilt all 20 incremental models, checked all
saved solver parameters and responses, recomputed achieved integer margins,
verified every shifted completion row, recounted all 1,200-entry numerical
ordinary vectors, and reconstructed every learned plane by exact column sums.
It also verified the full raw-file hash inventory and total solver budget.

The achieved normalized margins ranged from 2.220819 to 23.96. The heavy tuples
changed 22 through 28 blocks from the prior incumbent, reaching distant states.
Their smallest recomputed LP residual was 18.723394713738. The existing best
reported objective remains 5.575882992498541. This bounded pilot found neither
an improvement nor a fractional completion. It does not establish that all
maximum-margin searches fail; the master optima were not proved.

These scripts perform readback, finite reconstruction and arithmetic only.
All files in this folder pass Ruff. The evidence concerns the fixed-anchor
regular four-sevenfold family and supplies no unrestricted lower-bound theorem
or 64-block covering witness.
