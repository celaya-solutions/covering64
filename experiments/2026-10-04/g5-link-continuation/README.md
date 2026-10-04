```
Document:    Fixed Matching-Graph Continuation Result
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      ab91836573255b04fe952cae5ecb3ac9c0b3d9caedee03fe486a5e31afffbb90
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Fixed matching-graph continuation

One independently gated continuation started from the prior best objective 11.500690015970484. It reused the frozen structural two-edge-switch generator, graph-5 first-link registry, fixed hub-pair targets `[7,5,5,5,5,7]`, and 255 previously checked graph-5 LP cache entries. Only the original 14 broad cuts ranked neighbors. No graph-1 cuts or cache entered this branch.

| Round | Generated | Accepted | Rejected | Minimum LP objective | Selected improvement |
|---|---:|---:|---:|---:|---|
| 1 | 128 | 88 | 40 | 9.533204639679 | yes |
| 2 | 128 | 88 | 40 | 9.448398722490 | yes |
| 3 | 128 | 93 | 35 | 8.818415543402 | yes |
| 4 | 128 | 105 | 23 | 8.152937802509 | yes |
| 5 | 128 | 105 | 23 | 8.279923931333 | no |

All five neighborhoods were completely evaluated, with every accepted neighbor returning OPTIMAL. The selected objectives were 9.533204639679104, 9.448398722490406, 8.818415543401665, and 8.152937802508724. The fifth neighborhood's smallest solver objective was 8.279923931332549, so the run stopped at the first complete neighborhood without an improvement.

The run used 465 fresh LP evaluations and 14 cache reuses, 61.726965584093705 cumulative solver seconds and 68.66431654104963 wall seconds. The authorized caps were 10 rounds, 1,000 fresh evaluations, 150 solver seconds, 200 wall seconds, one second per LP, and one worker. No exact fractional feasibility or covering witness was found.

The independent gate identified and corrected a pre-launch edge case: an exactly checked primal obtained from a merely FEASIBLE numerical result must retain that actual record without requiring numerical OPTIMAL status. Source v1.0.1 contains that fix; the first frozen source/manifest/preflight were preserved in ignored scratch storage before regeneration. No solve ran under v1.0.0.

The independent postcheck in `../g5-link-continuation-independent/` replayed all neighborhoods, registry decisions, 479 evaluation records, primal values, cache origins and the final cache. All large raw files remain in `experiments/scratch/g5-link-continuation-20261004/`, with their hashes in `result.json`.

The stopping result concerns only the accepted structural two-edge-switch neighborhood of the saved graph-5 heavy profile. Floating LP objectives and numerical OPTIMAL statuses do not constitute an independently checked global lower bound. Other neighborhoods, heavy profiles, graphs and unrestricted 64-block candidates remain outside this result.
