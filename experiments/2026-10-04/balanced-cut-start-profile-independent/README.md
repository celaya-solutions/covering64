```
Document:    Weighted Balanced Cut Start Diagnostic
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      81a8c3e03996521a649e54e9fcadc7179946b1bf72923e79a71689bc7c175344
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Weighted balanced cuts of the two native starts

Both starts pass every balanced-cut necessary bound. Across all 6,435 bisections,
H9/a0a737 has maximum excess cut weight 28 (28 maximizing cuts); H10/85f6 has
maximum 30 (5 maximizing cuts). The complete-cover bound is 32. This diagnostic
adds the weighted, unrestricted-degree statement and fresh start counts to the
simple degree-five case already in `scripts/check_independent_clebsch.py:99–125`.

For a block with k points in the left half, let p and t count its same-half pairs
and triples. Checking k=0,…,5 gives 2t=3p−10. For 64 blocks, T=3P/2−320.
A full cover requires T≥2·C(8,3)=112, hence P≥288.

Every pair in a full cover occurs at least five times: its blocks must cover the
14 third points, three per block. The nonnegative weighted pair excess is
λ−5, and its total is 64·C(5,2)−5·C(16,2)=40. A balanced cut of weight w leaves
P=5·56+40−w=320−w same-half pair incidences, proving w≤32 without a regularity
or simple-graph assumption.

For a partial family, write h for same-half holes and q for repeated same-half
triple excess. The exact relation is 2q=96−3w+2h; the checker verifies it on
every bisection. Neither start is excluded. Passing is necessary, not sufficient.
No global infeasibility, new cover, or all-relabel conclusion follows.

Reproduce with `uv run python experiments/2026-10-04/balanced-cut-start-profile-independent/check.py`.
The checker pins both input hashes, checks all six block types, and enumerates
exactly one representative of each complementary pair of balanced partitions.
