```text
Document:    Independent Core Overlap Cap Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      34aea5705a29667aa6ac7f02c4823e5306daf1f37fd164ba41219a16931536b4
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Verified cap: at most 55 blocks from either current core

The saved exact four-removal certificate and its standalone standard-library
checker are present. A fresh isolated replay passed. It checked 8,337 symmetry
representatives covering all 487,635 four-block removal sets, using a verified
60-element subgroup that preserves the specified 60-block core. Every exact
dual bound exceeds eight; the smallest is 2,035,711 / 250,000. No representative
is uncertified. No optimizer was used in this audit.

The complete certificate has SHA256
`9997df71457bd6f4ca5567032cd026e3956d29235515acc330f05fddc6d9c298`.
It binds the canonical core SHA256
`7011e57be2714b1e1a16d4419ecb55a0160e25806f5db5dd786891aa17d0a5db`.
The saved checker reconstructs all 560 triples and all 4,368 possible added
blocks, checks the dual weights with integer arithmetic, and rejects incomplete
or overlapping removal-orbit coverage. The `lp_status` metadata is not used as
proof. `replay.json` preserves its fresh output; `audit.json` binds the source
bytes and the current pilot manifest.

## Why the cap follows

Suppose a 64-block cover contains at least 56 of the core's 60 blocks. Choose
any 56 of those retained core blocks. Their complement is one of the certified
four-block removal sets. Its certificate assigns nonnegative rational weights
only to triples missed by those 56 blocks. The total weight is greater than
eight, while every possible additional block has weight at most one. The other
eight blocks therefore cannot cover those missed triples. This contradiction
proves that every 64-block cover retains at most 55 blocks from this core.
This argument also applies to a cover with fewer than 64 blocks, since its
remaining addition budget is no larger.

The argument does not assume that the other eight blocks avoid the four removed
core blocks: the capacity check includes the entire block universe. Thus the
certificate for exactly 56 chosen core blocks excludes every larger retained
subset too.

## Current labels and recommended rows

The identity map and the point map below reproduce the two `core_rows` in the
frozen six-hole pilot manifest exactly, in zero-based lexicographic block order:

```text
point:  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16
image:  1  7  2 10 15  3  8 11  4  9 12 16 14  6  5 13
```

For each map, the audit checks bijections on all 4,368 blocks and 560 triples,
all 43,680 block-triple incidences, and recovery of the original core by the
inverse map. Hence transporting every residual dual and removal set preserves
the proof. The cap is valid for each of these two cores and any other point
permutation image.

The warranted model rows are `sum(x[b] for b in core_rows[i]) <= 55` for both
`i = 0, 1`. These necessary conditions can be used with all block variables
released. They neither impose an incumbent's incidence pattern nor limit the
distance from a hint.

Seven damaged controls were rejected: a changed target, a wrong core hash, a
nonpermutation generator, a repeated orbit, a missing orbit, a lost strict dual
bound, and a repeated dual weight. The existing five-removal scan covered only
909 classes, so it does not justify a cap of 54. This audit proves the stated
core-overlap restriction; it does not prove global nonexistence of a 64-block
cover. No model was built and no search was launched here.
