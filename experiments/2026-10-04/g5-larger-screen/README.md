```
Document:    Fixed-g5 Larger-Neighborhood Finite Screen
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      ff21775c10db28fccb100a41323ec51966edbb6fd8ded5a7a9cf348c7e99c26b
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Prepared fixed-g5 larger-neighborhood screen

Starting from the checked matching-graph best elastic objective 8.152937802508724, this solver-free preparation enumerates three finite neighborhoods and screens them using exact rational planes. It reuses the audited matching first-link catalog and 109-class exclusion registry. Graph 5 has hub-pair targets `[7,5,5,5,5,7]` for hubs 4,8,12,16 in lexicographic pair order.

The 720 conditional planes come only from the 720 independently checked graph-5 LP cache entries: two initial diagnostics, 253 fresh first-descent LPs, and 465 fresh continuation LPs. Exact signed row weights are bounded by their common denominator 1,000,000, so each plane supplies an exact elastic-residual lower bound. The 353 previously checked broad planes are separate inputs. No graph-1 conditional plane or graph-1 cache entry is used.

| Neighborhood | Structurally valid | Registry safe | Already cached | Positive combined bound | Unexcluded |
|---|---:|---:|---:|---:|---:|
| Proper three-edge switch | 680 | 492 | 14 | 492 | 0 |
| Two anchors with a two-edge switch each | 6,122 | 4,106 | 82 | 4,106 | 0 |
| One complete seven-edge link replacement | 46,436 | 46,436 | 128 | 42,940 | 3,496 |

All 492 proper three-edge states have positive graph-5 bounds; the smallest is exactly 1910640/1000000. All 4,106 paired-anchor states have positive bounds; the smallest is 2578784/1000000. The 3,496 unexcluded whole-link states are all uncached. The broad planes alone are nonpositive on every state in these three lists, so adding them does not change these counts.

Whole-link enumeration visits all 29,970 matching link catalog entries for each anchor, rejects 18,360 registry-excluded entries per anchor, and removes one unchanged link per anchor. There are 11,609 retained replacements per anchor. Proper three-edge states are contained in the whole-link list; paired-anchor states are disjoint from it. All labels and global block IDs retain the existing one-based point and zero-based lexicographic block conventions.

`count.py` and `envelopes.py` preserve the preparation sources. Sorted candidate, score and unexcluded lists are gzip artifacts. The original full certificate bundle is 42.2 MB and remains outside Git in ignored scratch storage. `g5-cuts.compact.json.gz` keeps exact signed weights and rows; `restore_bundle.py` reconstructs the identical full bytes, checked by SHA256. `archive.json` records the raw bundle and broad-reference paths and hashes. No original experiment artifact was changed.

These are preliminary exact-arithmetic screen results pending a separate independent finite replay. A positive bound excludes zero residual only for that fixed graph and candidate heavy tuple. A zero bound is inconclusive. This preparation performs no LP or CP optimization, asserts no global lower bound, and does not enumerate all heavy tuples, larger exchanges, other hub graphs or unrestricted 64-block covers.
