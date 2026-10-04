```
Document:    Finite Completion Screen for Pinned Affine Point Links
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      fa11959b4b909504da10518deaa8803dc7d84253f6a50c4a8af26d2d300a1b79
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

Exact finite support counting rules out completion of 249 of the 256 explicit
twenty-pentad partials saved in the sibling `clebsch-point-link-construction`
folder, using each partial's fixed recipe excess profile. Seven partials
survive this screen. Survival is not a feasible completion. The exclusion
applies to each exact pinned partial, not to every local decomposition of
the same class, every affine embedding, or the whole excess profile.

## Complete finite domain and sound deductions

For each saved profile seed and point p, reproduce its twenty blocks from the
canonical witness and the saved bijection, then verify the partial hash.
Its point-containing triple rows are already satisfied exactly. Subtract the
local outside-triple counts from global demand 1+1_H. This leaves 455 rows,
nonnegative integer demands, total demand 440, and 44 distinct blocks required.

Enumerate all C(15,5)=3003 pentads avoiding p in global lexicographic order.
A candidate containing any zero-demand triple is impossible, so remove it.
For each remaining positive triple row with demand d, count all remaining
candidate blocks containing that triple:

1. If fewer than d candidates remain, this exact partial cannot be completed.
2. If exactly d candidates remain, every one of them is required.
3. If those required blocks together exceed any triple's remaining demand,
   this exact partial cannot be completed.
4. Otherwise fix all required blocks, subtract their incidences, remove fixed
   blocks and newly impossible blocks, and repeat.
5. If no row forces a block and no contradiction occurs, report that the
   partial survives this finite screen. Make no feasibility claim.

These deductions require binary block selection, positive unit incidences,
and exact triple demands, all of which hold in this fixed-profile branch.
There is no symmetry assumption beyond fixing the explicitly supplied partial.
No optimizer, native search, random generator, time limit, or solver is used.

## Results and replay

Initial allowed pools contain 180 to 493 blocks. The first pass finds 144
cases with insufficient support and 201 with a forced conflict (these groups
overlap). At most three support-counting rounds per case are needed. Final
outcomes are 173 insufficient-support contradictions, 76 forced-conflict
contradictions, and seven survivors. All sixteen partials at point 1 are
excluded after propagation.

The survivors, listed as (profile seed, point), are:

| Profile seed | Point | Link class |
| --- | --- | --- |
| 0 | 10 | C4-leaf |
| 40 | 13 | triangle-path2 |
| 4 | 7 | C4-leaf |
| 18 | 3 | C4-leaf |
| 16 | 3 | C4-leaf |
| 16 | 8 | C4-leaf |
| 60 | 3 | triangle-path2 |

Run `uv run python experiments/2026-10-04/clebsch-affine-link-support-screen/screen.py`
from the repository root. `cases.json` saves all 256 initial partial pins,
candidate-pool hashes, every propagation round, and explicit final deficiency
or conflict witnesses. Forced-block records identify the tight triple row,
its demand, and its entire support list. Global five-block IDs are zero-based
in lexicographic order. Candidate-pool hashes use sorted IDs separated by
ASCII spaces and terminated with LF. `summary.json` pins source and input
hashes and records all outcomes. `files.json` pins the frozen folder.
