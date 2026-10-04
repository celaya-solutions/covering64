```text
Document:    Complete Heavy Template Native Construction Design
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      09e746913b33c5d2b3ae52f3df53cfbeb1f7baf0bcaaa5c31ab48a5dcc326189
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Complete-template native construction proposal

Use four independently selected audited heavy-link templates and 36 ordinary blocks. The anchor triples are {1,2,3}, {5,6,7}, {9,10,11}, {13,14,15}; hubs are 4,8,12,16. Every template contributes seven blocks through its anchor triple, own-hub degree two and each other outside-point degree one. Across four templates, anchor points have degree ten and hubs degree five. Ordinary blocks must therefore supply anchor degree ten and hub degree fifteen. The final 64 blocks all have degree twenty.

Both audited108 catalogs were checked directly: matching has 12,042 templates per group; cycle has 25,020. Every template has the same required incidence vector within its group. Whole-template replacement preserves degrees without a coupled trade. Exactly 1,200 ordinary five-blocks meet each anchor triple at most once; none is fixed zero in either normalized base matrix. Heavy blocks cannot collide across groups because two full anchor triples need six points. Ordinary blocks cannot collide with a heavy block. Explicit duplicate checks remain mandatory.

The existing generic regular heuristic preserves degree twenty but can change heavy links. The reduced-family heuristic models one fixed heavy link, three thirteen-block local families and eighteen outside blocks. The completed fixed-link/profile heuristic has audited two-block redistribution, directed swaps, cycles, rollback and saved-state checks. The new source will reuse those move principles separately, without modifying completed sources.

A guaranteed seed uses three disjoint length-twelve orbits under four-group rotation and simultaneous three-anchor rotation. Orbit block types have anchor counts (4,3,3) or (4,4,2). Every anchor then has ordinary degree ten and each hub degree fifteen. The constructor may select the best of these orbit triples for an independently selected heavy-template tuple. Rotation is seed construction only. All ordinary proposals are allowed to break it; move connectivity is not proved.

Search moves are: a missing-triple-directed ordinary two-block swap; ordinary symmetric-difference redistribution; ordinary point cycles across three to six blocks; and replacement of one complete seven-block template by another from that group's frozen catalog. Each move checks exact zero degree change, selected-block uniqueness and the allowed ordinary family before mutation. A targeted template proposal may choose a template containing the outside edge of a missing triple with one anchor point; global random template proposals retain access to the whole catalog.

Actual missing triple count is the primary objective. Initial pilots will use no hard pair-profile restrictions or hole ceiling. Actual pair counts are recorded. This is a construction heuristic using branch-derived catalogs, not exhaustive matching/cycle branch membership. Every zero-hole state is saved and checked by both covering verifiers, even if later soft penalties are added and remain nonzero.

Freeze source, compiler, complete catalog packs, seeds, random seeds, budgets and hashes. Require strict native parsing, independent catalog/seed checks, warning-clean and ASAN/UBSAN builds, forced moves for every type, inverse rollback and malformed/duplicate controls. Independently recount every saved state and replay operation descriptors; run both covering verifiers and retain full outputs. The independent source gate precedes one300-second matching and one300-second cycle pilot, at most two single-thread processes. No negative result excludes a case.
