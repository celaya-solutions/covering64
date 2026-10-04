```
Document:    H6 Radius Four Deletion Upper Screen
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      c072d75b34c1b5ab1659ea18f32ee346a47620f61f06da6f73ae80054c46afb2
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Workload assessment only

One authorized deletion-only screen completed all 635,376 four-block deletion
sets from the pinned H6 exact64 family. It took 1.42649 native seconds, within
its 28-second internal budget and 30-second process watchdog. No replacement
tuple was enumerated; distances one through three were not repeated. All frozen
earlier artifacts remain unchanged.

The input SHA256 is
`2d018ffa5e3e424193a4197b23891b52fa59b7ca411d06108e0ab1666bb85855`.
Actual source revision was `d2bfd843889e8b6f549881c7493fae196383b170`.
The full command, compiler version, flags, source and binary hashes, raw log
hashes, wall time, progress, and final counters are in `receipt.json`.
The ignored binary and raw logs are under
`experiments/scratch/h6-radius4-deletion-upper-screen-20261004`.

The screen tracks original triple coverage and the number of current holes hit
by every one of the 4,304 original nonmembers. Losing a triple updates its
carriers once, on the positive-to-zero crossing; restoration reverses that
update. A score histogram gives the four largest scores. Their sum is a safe
upper bound on the union coverage of four additions. For target H<=5, each
addition must individually score at least demand minus the three largest global
scores. The screen counts all eligible additions at or above that floor, then
sums the number of their unordered four-subsets. These subsets are only a
workload bound; overlapping gains can still prevent success.

Results:

- 633,208 deletion sets fail the safe top-four upper bound.
- 2,168 deletion sets survive, with necessary-floor pools of 4 to 364 blocks.
- The naive addition loop would test 3,697,940,975 unordered four-subsets.
- Four pools of size 364 alone account for 2,877,879,004 subsets (77.82%).
- Residual hole counts range from 24 to 46, so the existing 64-bit mask is safe.
- All initial coverage counts, scores, and histogram entries were restored.

For the unchanged tuple loop to finish in 60 seconds, it would need more than
61.6 million completed tuples per second plus deletion setup, recursion, timer,
and output overhead. No tuple-throughput benchmark was run. A reliable 60-second
completion should therefore not be assumed from the fast deletion screen.

A sibling exact-distance-four enumerator could retain the same mathematical
rules with four score slots, four-block deletions/additions, and radius-four-only
completion accounting. It would need a separate runner, controls, and gate;
none were prepared here. A safe possible improvement is to prune partial
addition choices using current union coverage plus an upper bound for remaining
gains. That improvement is a proposal only and needs its own completeness check.

These counters do not establish whether any surviving deletion set admits an
improvement, a cover, or an unrestricted impossibility result. Independent
recount is separate from this producer receipt.
