```
Document:    Independent Fixed-g5 Larger-Neighborhood Exact Screen
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      46caa8077676101af5aef41c9b001f628ecc8848fd3d88f372051036ff5ed2b4
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Fixed-g5 larger-neighborhood audit

`enumerate.py` independently reconstructs proper three-edge moves, paired
single two-edge moves on different anchors, and complete replacements of one
anchor link. Whole links are generated directly by choosing the hub's two
neighbors and a perfect matching on the remaining vertices, rather than by
reading the source runner's link catalog. All labels remain 1-based, and block
indices follow the same zero-based lexicographic order.

The independent enumeration gives 492 registry-safe proper-three states,
4,106 paired-two states and 46,436 whole-link states. The entire state arrays
match the source screen. The checker replays all 720 saved g5 signed-row planes
using integer coefficients and rational gaps, bounds the weight norm, binds
each plane to the checked final cache, and keeps the 353 previously audited
broad planes separate. It recomputes every envelope score and survivor list
using overflow-checked integer arithmetic.

| Neighborhood | Registry-safe states | Exact positive bound | Unexcluded | Minimum bound |
| --- | ---: | ---: | ---: | ---: |
| Proper three-edge | 492 | 492 | 0 | 1.910640 |
| Paired two-anchor | 4,106 | 4,106 | 0 | 2.578784 |
| Whole link | 46,436 | 42,940 | 3,496 | 0 |

All 3,496 unexcluded whole-link states are absent from the checked 720-entry
g5 cache. A zero lower envelope is inconclusive. Positive bounds exclude exact
fractional completion only for the finite heavy patterns in this fixed-g5
branch; this is not an exclusion of the entire family or a global covering bound.

The compact signed-row archive independently reconstructs the full 42,202,869-byte
bundle with its original hash. The full bundle and independent state archive
remain in ignored scratch. No optimizers run in either audit script. The saved
receipts are protected against overwrite; `audit.json` includes all 720 exact
source-gap receipts.
