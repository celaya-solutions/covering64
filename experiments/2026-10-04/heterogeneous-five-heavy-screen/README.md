```
Document:    Two-Partition Five-Heavy Saved-State Screen
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      036461529208b48468259b02ba6f6e82396cc5290c92acca2a13ee9224d90050
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Two-partition five-heavy screen

Both final states from the core-avoiding pool still trigger the previously established five-heavy obstruction on the mapped partition: five vertex-disjoint triples each appear at least six times, and at least two appear at least seven times. The elite final has multiplicities `[6,7,7,7,6]`; the expanded final has `[7,7,7,7,6]`. Deleting one block of the known 60-block core did not remove this stronger pattern.

The original partition, extracted directly from the saved core, is `(1,3,6), (2,14,15), (4,8,10), (5,13,16), (9,11,12)`. Its mapped partition in the same order is `(1,2,3), (5,6,7), (9,10,11), (13,14,15), (4,12,16)`. Each partition consists of five disjoint triples on 15 points.

| State | Holes | Original partition counts | Mapped partition counts | Avoids both named obstructions |
|---|---:|---|---|---|
| unrestricted-old-3 | 3 | [7, 6, 7, 7, 7] | [1, 1, 1, 1, 1] | no |
| unrestricted-new-3 | 3 | [1, 1, 1, 1, 2] | [7, 7, 7, 7, 6] | no |
| regular-5 | 5 | [1, 1, 1, 1, 2] | [7, 7, 7, 7, 6] | no |
| regular-8 | 8 | [6, 7, 7, 7, 6] | [1, 1, 1, 1, 1] | no |
| sqs-23 | 23 | [1, 1, 1, 1, 1] | [1, 2, 2, 1, 1] | yes |
| native-cycle-12 | 12 | [1, 1, 1, 1, 2] | [7, 7, 7, 7, 6] | no |
| g1-initial-13 | 13 | [1, 1, 1, 1, 2] | [7, 7, 7, 7, 6] | no |
| g1-best-17 | 17 | [1, 1, 1, 1, 2] | [7, 7, 7, 7, 6] | no |
| g5-raw-17 | 17 | [1, 1, 1, 1, 2] | [7, 7, 7, 7, 0] | yes |
| g5-score-19 | 19 | [1, 1, 1, 1, 2] | [7, 7, 7, 7, 1] | yes |
| elite-core-pool-final | 5 | [1, 1, 1, 1, 1] | [6, 7, 7, 7, 6] | no |
| expanded-core-pool-final | 5 | [1, 1, 1, 1, 2] | [7, 7, 7, 7, 6] | no |

Among the ten initial seeds, only `g5-raw-17`, `g5-score-19`, and `sqs-23` avoid both named partition obstructions. The fewest-hole such seed is `g5-raw-17`, with 17 holes. These are partial-state screens, not claims that any of these seeds can be completed without replacing blocks.

All 12 source states were already checked by both covering verifiers. This read-only audit rebinds their hashes, confirms 64 distinct valid blocks, and recomputes every partition multiplicity. No optimizer or unrestricted partition/isomorphism search ran. Avoiding these two particular labeled obstructions does not prove absence of every possible relabeled five-heavy obstruction, and this audit does not replace the existing obstruction proof.
