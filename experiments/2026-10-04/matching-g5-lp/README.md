```
Document:    Two Fixed Matching Graph Elastic Diagnostics
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      aacc437744a484726c5e6e55d8662ccd9796cd6b742db82652ceafa3f4dd82d4
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

Exactly two authorized elastic LPs ran, each with one worker and a one-second
cap. Both finished OPTIMAL; neither found an exact fractional feasible point.

| Heavy tuple source | Fixed graph-5 objective | Exact positive gap | Solver seconds |
| --- | ---: | --- | ---: |
| Native soft raw best, 17 holes | 15.06922063054413 | 15069111/1000000 | 0.132980250 |
| Native soft score best, 19 holes | 15.317006713016973 | 3063381/200000 | 0.129158250 |

The raw-best tuple is slightly better by this completion-LP objective, despite
the other seed's lower native soft score. This is a comparison of seed fitness,
not proof that either can be completed. Each exact certificate excludes only
its fixed 28 heavy blocks under graph 5. These graph-specific certificates
remain separate from the broad all-graph cut bundle.

Both models retain 1,200 ordinary columns and 697 rows, with exact hub-pair
targets (7,5,5,5,5,7) on (4,8), (4,12), (4,16), (8,12), (8,16), (12,16).
The independent pre-run gate reconstructed every support, bound, variable ID
and registry link map, and checked the frozen one-second/one-worker source.
The source's originally proposed ten-second budget was changed before any
optimization, then the updated source/manifests were frozen for that gate.

Each producer certificate was separately replayed by the existing exact
pinned-profile checker. A further independent postcheck replayed all 1,200
ordinary values, 1,390 slack values, all 697 rows, objective values and signed
dual certificates. Its receipt is in the sibling `matching-g5-lp-independent`
folder. Both runner exits were normal and stderr was empty. Total solver time
was 0.262138500 seconds; no additional LP or integer search ran here.

The top and case manifests describe the prepared state with zero prior solver
calls. Per-case `launch.json`, `result.json` and `receipt.json` record the one
actual call each. The immutable launch marker prevents an accidental repeat.
Original and elastic models, full solver logs, saved primal/dual values,
all slack values and frozen source remain in
`experiments/scratch/matching-g5-lp-20261004`. `files.json` and `raw-files.json`
bind the compact and ignored raw artifacts respectively.
