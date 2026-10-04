```text
Document:    Two-Point-Star Covering Repair
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      aed5867923278161df83a19be8574ca3456fc499bcc4886102c86381e8e1e85d
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Two-point-star repair

Original frozen preparation. It was never launched. Independent review found that its vector checker accepted float and bool values. This version is superseded by v2; its models are unchanged.

The starting family is the independently checked H12/D26 descent endpoint, SHA256 `f8d2525acd5dcb7db6e60bbff70b60612b12a0a6500bd25ac0841b4de18c955d`. Both models retain all 4,368 block variables in lexicographic order. For each pivot pair, all 2,002 blocks disjoint from it are fixed to their original memberships. The other 2,366 block variables remain free. Each neighborhood retains 29 fixed selected blocks and rebuilds 35 blocks.

Each model has 4,928 variables and 1,242 rows: exact cardinality 64; 560 two-way hole indicators; the necessary pair-count floor five; and at most 12 holes. The objective minimizes the exact number of holes. All block and hole variables receive a complete feasible starting hint. No single-triple, quadruple, stronger-pair, core or degree-profile restriction is imposed. Partial outputs may therefore fail those additional diagnostics. These are local neighborhoods, not unrestricted models or complete paths through search space.

The declared campaign has two sequential 60-second, four-worker calls, each starting independently from the same D26 family. Pivots are (6,14), then (1,9), with seeds 2026105301 and 2026105302. Each call has an 80-second outer watchdog and five-second termination grace. There are no retries or budget transfers. A cover, incomplete child or child failure stops the campaign. UNKNOWN/timeouts are inconclusive; no solver response alone establishes a theorem.

Callback vectors and the final feasible vector are saved atomically. The parent checks every domain and active linear row, then reconstructs a witness and calls both the package verifier and standalone checker. A zero-hole callback stops native search; it is only accepted as a cover after both external checks pass. Exact sources, model hashes, seed, solver version, command, parameters, logs and response are retained. Large models and raw outputs stay in ignored scratch.
