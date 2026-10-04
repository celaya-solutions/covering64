```
Document:    Prepared Compact Full-Universe Pair-Two-Triple Count Model
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      58349b77c590a831709d40a91bf9f0dbd4ed3eac09f7957166510ba534058e6c
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Prepared stronger compact count model

This separate sibling has 5,608 variables and 14,404 rows. It is prepared for one
independently gated run. The weaker quadruple-count sibling remains preserved,
unrun, and superseded for execution. No preparation step called an optimizer.

All 4,368 lexicographic block variables remain free, with cardinality exactly 64.
Point labels are one-based. Exact counts cover all 120 pairs and 560 triples.
Their domains are [5,64] and [0,64]; the upper bounds follow from cardinality 64.
There are 560 exact hole flags, with two enforced rows per triple expressing
`hole iff triple_count == 0`. No quadruple variables remain.

The rows comprise one cardinality row, 680 count definitions, 1,120 hole rows,
1,680 single-triple cuts, 10,920 two-triple cuts, and the three independently
checked core caps at 55. The objective remains `65*holes + original_core_overlap`.
No equal-degree, incidence, family, symmetry, global DP, or named partition
restriction is imposed. Every saved output is still globally profile-scanned.

## Completeness and stronger local cuts

For each pair P and outside point a, retain `3*c(P)-c(P+a)>=13`.
For each pair P and unordered outside pair {a,b}, impose
`3*c(P)-c(P+a)-c(P+b)>=12`. The latter rows are ordered first by P, then by {a,b},
with both orders lexicographic.

The exact identity for the stronger row is
`3*c(P)-c(P+a)-c(P+b) = sum(c(P+x) for x outside P+a+b)`.
There are twelve terms, each at least one in every full cover. Thus these rows
preserve every cover without regularity or incidence assumptions. Also,
`c(P+a)+c(P+b)>=2*c(P+a+b)` by containment, so each new row dominates the former
quadruple row. Removing quadruple variables removes only uniquely defined
auxiliaries, while the stronger cuts preserve every full cover.

Given any 64-block cover, choose its 64 block indicators, set all exact counts
to their containing-block sums, and all hole flags to zero. Every variable is
available. Pair counts are at least ceiling(14/3)=5 because each block through a
pair covers three of its fourteen required triples. The single- and two-triple
rows follow from the stated identities. The three core caps follow the bound
and relabeling proof receipts frozen with this preparation. Therefore every
valid 64-block cover remains represented. A near-cover, timeout, or native
infeasibility status is not an independently checked global lower bound.

The independent stronger-cut receipt is
`db490b9d3cd3500eb2c85d36f803a73667ceed00e5251932608e7d1150e7099b`.
Its 3,974,880 column identities and dominance checks pass. The original local-cut
proof and core-cap proofs are also bound in `manifest.json` and snapshotted.

## Incomplete, infeasible guidance

The exact same six-hole guidance is retained, SHA256
`797dada195b23eecc808798eb12c8e4e7ccd7edd026fbdf22dea5b341f9ea2de`.
Only all 4,368 block indicators are hinted, with 64 ones; 1,240 auxiliaries are
unhinted. No variables are fixed by this hint. The unique full count extension
violates four single-triple rows and 62 two-triple rows. It is explicitly
infeasible, and the solver may repair or reject it. The hypothetical objective
392 is not a feasible incumbent. `guidance-diagnostic.json` preserves every
violated row and binds the diagnostic extension vector.

## Frozen files and execution contract

| Item | SHA256 |
| --- | --- |
| Preparation source | `dd615064bcf96fd28a62fe13859874c417ff050ff60198bf62a1f4efdb8115ae` |
| Manifest | `82372b924493eed1e3a24c48e580d0b15796cc1d2c50bbe71b400bee23910aad` |
| Model | `2901bb03bc1b12a9ab950bf93b1e3bd0ef84760ab9ce87ce8fc0bb6b59d45d87` |
| Parameters | `a72db619575952d0899a8b1c65a9196f5c025c05e2b153ab019988ebff7c5e3f` |
| Runner | `0445dff332c3e8b817c843ea3d82c56f1b95b85ec7918213af6dc14ab99e6803` |

The model is 5,437,679 bytes and lives under ignored
`experiments/scratch/compact-pair-two-counts-20261004/`, with parameters, guidance,
diagnostic vectors, source/input snapshots, and a frozen runner copy. The local
index `files.json` binds preparation documents and receipts. Build measurements
are preparation-only and make no propagation or runtime claim.

The budget is one 120-second run, four workers, seed 2026104301. The runner
requires a passed gate binding preparation source, runner source, manifest,
model, and parameters, and refuses existing runtime outputs. It reads the saved
model and calls the solver exactly once. It saves every callback improvement,
distinct best-score tie, complete final vector, native response, sources, hashes,
logs, and parameters. It recounts counts, holes, core overlap, and the actual
global five-heavy partition maximum for each state. It stops on zero holes;
both covering verifiers must approve any covering witness.

The result records first-feasible callback time and native hint, search-start,
and first-solution messages, together with the incomplete/infeasible guidance
flags. Runtime comparisons must distinguish this need to find a first feasible
state from the earlier DP runs that began with feasible complete hints.
