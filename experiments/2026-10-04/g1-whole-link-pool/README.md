```text
Document:    Fixed-g1 Whole-Link Survivor Pool Screen
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      168d0eed0a6bd06f7da855c562feb10bf7fcf4bb563529fb557700fddfc97731
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```
# Bounded survivor-pool screen

The frozen pool contains exactly 757 previously unexcluded, registry-safe whole-
link replacements of the fixed-g1 local minimum. There are 72 replacements of
six edges and 685 replacements of all seven edges in one anchor link. The
independent gate checked all 527,629 shifted rows, 3,028 link classifications,
profile hashes, ordering and absence of cached evaluations before launch.

All **757 fresh GLOP calls returned numerical OPTIMAL**. No call reached numerical
zero, and none improved the branch incumbent **7.52051548546158**. The best new
score was **10.613462674257228**, at rank 648; the largest was 18.814834929517954.
There were no improving stitched integer families and no covering witness.

Actual cost was **101.28901211789344 solver seconds** and
**110.18559237499721 wall seconds**, below the 160/200 caps. Every call used one
worker, a one-second limit and seed 2026104. OR-Tools was 9.15.6755. Launch
revision was `c80235d7fc403c6bdb9a7d06cf8134f6a267fae9`.

The gate and postcheck in `../g1-whole-link-pool-independent/` independently
replayed every saved numerical vector, row/profile/registry binding and budget.
The manifest and pool IDs are tracked here. Full registry receipts, all primal
and dual vectors, source snapshots and execution logs are in the manifest-bound
ignored preparation and execution directories. No optimization was repeated.

The separate `../g1-whole-link-certificates/` replay converts the saved duals into
exact g1-conditional certificates. This numerical screen alone does not prove
infeasibility. Neither the screen nor the subsequent finite certificates prove
that the branch score is optimal over all whole-link replacements: many states
already had positive feasibility lower bounds below the incumbent score and
were intentionally outside this 757-state pool.
