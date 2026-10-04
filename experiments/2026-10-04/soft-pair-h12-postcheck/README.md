```text
Document:    Independent Soft H12 Runtime Postcheck
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      3ffefd8a726d54e6909550196f3e5ff743cf907a7df43a40a392f42ca2324370
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent outcome

The single authorized soft-model run ended FEASIBLE after 300.012574 solver
seconds, using 4 workers and seed 2026104901. Its three callbacks and final
response contain two distinct 64-block families. Neither is a cover: both
leave 12 triples uncovered. Actual compact and expanded pair deficits improved
from 34 to 32; no actual-zero callback occurred. The objective lower bound was 0.
These are soft-model observations, not a global covering-number lower bound.

| Saved state | Holes | Actual D2max | Actual D2sum | Solver deficit sum | Canonical objective | Solver objective | Auxiliary slack |
|---|---:|---:|---:|---:|---:|---:|---:|
| Callback 1 |12|34|34|34|19086|19086|0|
| Callback 2 |12|32|32|33|17964|18525|1|
| Callback 3 |12|32|32|32|17964|17964|0|
| Final |12|32|32|32|17964|17964|0|

Callback 2 is valid: the soft auxiliary variables are lower bounded and may
contain slack. Its block family already has actual deficit 32. The independent
checker distinguishes those canonical block-derived deficits from the solver
assignment, so removing that extra auxiliary unit is not mistaken for a further
improvement in the actual family. Callback 3 and final have identical canonical
vectors and family bytes.

The improved family SHA256 is
`cadb86e4f2243eada269dc314bca0bc5c238f5b0ca2bd9525dd0b67aad24c970`.
Its minimum pair count is 5, D3=D4=0, four core overlaps are `[1,1,1,2]`, and the
independently recounted disjoint-triple profile maximum is 0. These necessary
conditions do not fill its 12 holes. Because actual D2max remains 32, the proposed
conditional hard-model extension of a zero-deficit hint is not triggered.

# Independent checks

The checker imports no producer metric or vector helper and calls no optimizer.
It adapts the prior independent `soft-pair-two-postcheck` checker, with its source
hash recorded in the receipt. It binds the actual model, parameters, hint,
producer source, input evidence, frozen proofs, root gate, result, raw logs,
callback metadata, witness files, and full vectors by hash.

For all four saved vectors it checks 5,728 integer domains, every one of 14,405
model rows including enforcement conditions, all 13,845 active rows, and the
model objective. It independently rebuilds every pair/triple count, hole bit,
all 10,920 expanded pair deficits, compact maximum deficits, D3/D4 values, core
overlaps, and profile maximum from the 64 selected lexicographic five-blocks.
Canonical values are checked separately from permitted positive solver slack.
The final vector is compared directly with the solver response.

Both unique families passed both independent covering checks using actual
cardinality 64. They correctly report incomplete families with 12 holes. Saved
witness text matches the recounted canonical blocks. Callback ordering,
nonincreasing solver objectives, actual-zero stop flags, configured timing,
and the single solver-start/response-summary log pair all agree.

Eight damaged full-hint controls were rejected: shortened vector, noninteger
value, bad block domain, broken count identity, broken hole channel, negative
deficit, understated required deficit, and broken cardinality. A valid positive
slack control was accepted and kept the same actual family metrics. Scoped
ruff and diff checks pass.

Postcheck SHA256:
`a27cd62205199d45621417e45f1320fbe6dbea077b00149ef0b5017b7231b16a`.
Result SHA256:
`b2af7c783fb889ee76cb2be10c9e3bb39c951b8a1884646333a20075f2f65132`.
Gate SHA256:
`be4b5b900e1de8238d70c4a7d88c17dcefa2c9d30b8d73655bbb25ca12820990`.
No producer file was changed and no search was relaunched. The native partial
start pilot overlapped this run, so elapsed times are not controlled comparative
performance measurements.
