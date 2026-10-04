```
Document:    Fixed Matching-Graph Descent Result
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      70c5de369f6eaf55ed076fe62efe0bc2b86c22a77f6466d8277ed635afbf7e62
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Fixed matching-graph descent

One authorized, independently gated descent ran from the 17-hole matching seed's 28 heavy blocks. It kept hub graph 5 fixed, with hub-pair targets `[7,5,5,5,5,7]` in lexicographic order on hub labels 4,8,12,16. The first-link registry was applied before every fresh LP. Only the original 14 broad cuts ranked candidates; no graph-1 cuts or cache entries entered this run.

The initial elastic objective was 15.06922063054413. Three complete rounds selected objectives 13.221637797152143, 12.594498845064832, and 11.500690015970484. Every evaluated LP was optimal, but every objective remained positive. No exact fractional completion or covering witness was found.

| Round | Structural neighbors | Registry accepted | Registry rejected | Evaluated |
|---|---:|---:|---:|---:|
| 1 | 127 | 86 | 41 | 86 |
| 2 | 128 | 86 | 42 | 86 |
| 3 | 128 | 84 | 44 | 84 |

The run used 253 fresh LP evaluations and 3 cache reuses, 33.94579962082207 cumulative solver seconds and 38.15049670799635 wall seconds. Limits were 3 rounds, 350 fresh evaluations, 60 solver seconds, 90 wall seconds, 1 second per LP, and one worker. It stopped at the round limit. The final state was not screened for another neighborhood, so this is not a local-minimum claim.

The independent gate and postcheck are in `../g5-link-descent-independent/`. The postcheck rebuilt all three neighborhoods, registry maps and shifted rows; replayed all 256 evaluations; and checked exact cache history and budgets without another optimizer call. Raw logs, primal vectors and floating dual vectors remain outside Git under `experiments/scratch/g5-link-descent-20261004/`; every raw hash is retained in `result.json`.

The best saved profile is a set of 28 pinned heavy blocks with a fixed matching graph. Its score is conditional on that graph and those pins. This artifact does not claim a new global lower bound or rule out other graphs, other pins, or the unrestricted 64-block problem.
