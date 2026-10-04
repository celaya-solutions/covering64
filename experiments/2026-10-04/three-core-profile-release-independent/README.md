```text
Document:    Independent Three Core Profile Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      55664a68608a338f9b5b17c70ba48c265038be4145a4957d434642ee162fbc66
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent three-core/profile audit

The preparation gate and result audit passed. The auditor made no optimizer
calls. The producer ran each declared case once with 120 seconds, four workers,
and seed 2026104103. Both frozen models release all 64 slots, preserve the prior
952-block and full 4,368-block pools, and minimize
`65 * holes + original_core_overlap`.

Each complete model was reconstructed independently: 4,958 Boolean variables
and 1,188 linear rows. The models contain the three independently proved
60-block core caps of 55 and three proved five-heavy profile restrictions.
All 30 threshold indicators have both implications checked. The third core is
bound to `third-core-independent/audit.json`; the third profile is the disjoint
partition found in the previous full-pool final. The exhaustive threshold
truth tables were replayed for all three partitions.

All 15 previously checked strong-core candidate paths were recounted, including
their pool membership. The best legal full-pool hint has ten holes but contains
block IDs 1151, 1278, and 2299 outside the adaptive pool. The declared hint rule
therefore selects different starting families: 13 holes for the adaptive pool
and 10 for the full pool. Both hints were checked by both covering verifiers.
These are two bounded construction attempts, not a controlled comparison of
pool size. Six damaged model controls were rejected before GO.

## Results

| Pool | Hint holes | Final holes | Final original-core overlap | Final objective | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| Adaptive 952 | 13 | 12 | 1 | 781 | FEASIBLE |
| Full 4,368 | 10 | 10 | 1 | 651 | FEASIBLE |

Both numerical objective bounds are zero. The adaptive and full calls used
120.01267079205718 and 120.0080802909797 wall seconds. The adaptive callback
saved 13- and 12-hole states; its final family is identical to the last saved
state. The full callback saved only its ten-hole hint, but the native final is
a different equal-objective family sharing 62 blocks with that hint.

All five saved/final records, representing four distinct families, passed
independent assignment, objective, core, and profile checks. Both covering
verifiers confirmed every family as a well-formed 64-block noncover with its
reported missing triples. Seven damaged native responses and three malformed
witness controls were rejected.

The global five-heavy scan found no obstruction in any record. The final core
overlaps are `[1, 7, 50]` for the adaptive family and `[1, 7, 55]` for the full
family. Each record has one necessary partition in the broader relabeled-core
deficit test; that result is inconclusive about other core images. The declared
242-image transposition screen finds no overlap above 55, with checked maxima
of 11 or 12. Its limited image set is not a full transport search. The reused
deficit scanner and its completeness proof are separately hash-bound in the
postcheck and artifact manifest.

## Point and pair diagnostics

`degree-pair-diagnostics.json` records all 16 point degrees and 120 pair counts
for both hints and both native finals. No model row was added during this work.

| Family | Minimum point degree | Points below 19 | Minimum pair count | Pairs below 5 |
| --- | ---: | ---: | ---: | ---: |
| Adaptive 13-hole hint | 19 | 0 | 4 | 5 |
| Adaptive 12-hole final | 19 | 0 | 4 | 5 |
| Full 10-hole hint | 19 | 0 | 4 | 3 |
| Full 10-hole final | 19 | 0 | 4 | 3 |

For a full cover, a fixed pair must occur with each of the other 14 points.
Each containing five-block provides three such points, so every pair occurs in
at least five blocks. The 15 pair counts incident to a point sum to four times
its degree. Thus that degree is at least `ceil(75/4) = 19`. These are necessary
conditions only; satisfying them would not prove that a family covers every
triple. The diagnostics simply identify remaining pair deficits in these four
already checked states.

All raw models, parameters, responses, logs, and launch files remain in ignored
scratch storage and are hash-bound by the audit. No cover or unrestricted
lower-bound theorem is claimed.
