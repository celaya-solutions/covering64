```text
Document:    Core-Avoiding Heterogeneous Block Pool Pilot
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      add3c2410c78fb6f86929a6d3af6f7845f433554dd8fdf0186d088ab965b43c6
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Core-avoiding pool construction

The preceding heterogeneous-pool pilot returned its original three-hole seed
in both 30-second runs. This separate experiment uses exactly the same
277-block elite pool and 337-block expanded pool, but adds two explicit
construction restrictions: each of the two mapped 60-block cores in the
checked seed inventory may contribute at most 59 selected blocks.
The maps and the 60 global block IDs per row are frozen in `manifest.json`.
No other incidence, degree, graph-family or symmetry constraint is added.

The complete hint is the checked regular five-hole seed, which shares zero
and 59 blocks with those two cores. All 4,368 block variables and 560 exact
hole indicators retain their original ordering. There are now 1,124 rows.
An independent delta gate must reconstruct both entire models and all hint
values before two runs of at most 30 seconds and four workers each.

This is a declared restricted construction search. A failed bounded run or
solver bound is not a global lower-bound proof. Every saved full state must
be checked with both existing covering verifiers before any covering claim.
Sources, seeds, model hashes and budgets are frozen; raw models and logs
remain under `experiments/scratch/heterogeneous-core-pool-20261004/`.

## Status

Both cases ran once for 30.028819 and 30.003867 seconds and returned FEASIBLE
with five holes and solver bound zero. Neither improved the five-hole hint.
Both callback states and both final equal-objective responses passed both
cover verifiers. The independent postcheck passed. Final ties have degree
histogram 19:3, 20:10, 21:3 and retain 59 blocks of the second forbidden core.
They still contain five disjoint triples covered at least six times, including
at least two sevenfold triples. Thus avoiding the two exact 60-block cores
did not avoid the broader previously proved five-heavy obstruction. That
separate read-only recount is saved in `../heterogeneous-five-heavy-screen/`.
These runs establish neither pool optimality nor a global lower bound.
