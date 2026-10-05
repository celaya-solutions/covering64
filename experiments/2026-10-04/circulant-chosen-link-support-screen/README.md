```
Document:    Bounded Benchmark of a Circulant Link Support Screen
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      10f255f29cd88443ef7e881dc66ba30c6f9baf67e1453988b2a5a19c7221c202
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

This stage prepares and benchmarks one finite support pass over the frozen
chosen-link catalog. The full 195296-pair run is not authorized or exposed
by this runner. No optimizer or iterative propagation is used. Preparation
freezes the source and input hashes before the benchmark begins.

## Exact case operation

For each (profile, partial) pair, start with all 3003 pentads avoiding point
1, whose global lexicographic IDs are 1365..4367. Reconstruct the 455 exact
outside triple demands as 1+1_H minus the eighty distinct outside triples
covered by the partial. The residual sum is 440, hence 44 more blocks are
needed. No point-avoiding block is excluded before the residual rows are
formed. Each row's initial support contains exactly 66 of the 3003 pentads.

Remove any pentad containing a zero-demand triple. Check that at least 44
candidates remain. For every positive triple row, count its remaining
support. Fewer supporting blocks than demand proves this pinned partial
cannot be completed. Support exactly equal to demand forces those blocks.
If the union of these immediately forced blocks exceeds any triple demand
or cardinality 44, that is also a contradiction. Otherwise the case survives
this single pass; do not claim feasibility or propagate the forced blocks.

Each exclusion records the actual deficient row, exact demand, and full
support list, or a conflicting row with the forced blocks and each tight
forcing row's complete support. Candidate masks are hashed as 376 bytes in
little-endian order; bit i corresponds to global block ID 1365+i. All records
include stable pair, profile, and partial IDs and operation counters.

## Deterministic benchmark and cap

Pair order is excess-link ID, then partial ID, then ascending compatible
profile ID. The manifest freezes 1000 pair ordinals floor(i*195296/1000),
for i=0..999, spread across the whole catalog. The benchmark has a ten-second
wall budget, including loading and output, and stops beginning new cases
at 9.75 seconds. It saves the completed ordinals, so a capped benchmark is
never reported as complete. There is no retry or hidden continuation.

Run `uv run python experiments/2026-10-04/circulant-chosen-link-support-screen/run.py prepare`,
then after the manifest is frozen run the same command with `benchmark`.
The compressed proof records are saved under ignored scratch. The tracked
benchmark receipt pins their hash, outcomes, counters, total elapsed time,
and a sample-based full-run estimate. The estimate is not a guarantee.
Root reviews this measured cost before authorizing a full finite run.

The scope remains all excess-graph isomorphism images of the four specifically
chosen canonical witnesses across the supplied 1300 profiles. This is not
all affine constructions, all local decompositions, or unrestricted covers.
