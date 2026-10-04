```
Document:    Independent Replay of the Best Fixed-Cycle Descent Tuple
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      a47c046821e487b42157150ffd20bcb82472bc62c60772d175ac954574cf129e
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

The selected fixed-graph-1 descent tuple has reported elastic objective
7.52051548546158. This check made no solver calls. It independently rebuilt
all 697 shifted rows and all 1,200 ordinary columns from the selected 28 heavy
blocks, checked the frozen numerical vectors and source hashes, and replayed
the graph-1 first-link maps. The four registry-open classes remain cycle-061,
cycle-061, cycle-086 and cycle-086.

Rounding the saved dual at denominator 1,000,000 produced 517 nonzero signed
row weights. The separate exact checker recomputed right side 7,520,474 and
box maximum 18, giving a strictly positive gap **940057/125000 = 7.520456**.
Eight damaged certificate controls were rejected. This is an exclusion of
the selected fixed heavy tuple under graph 1 only; it is not an all-graph cut
or a new first-link registry exclusion.

The saved primal was clipped to the exact [0,1] box and represented as exact
rational values. Recounting every elastic row then certified an upper bound
**7.520515486**. Thus the saved numerical objective has close exact lower and
upper checks. This is not an exact feasible point for the original rows,
and no covering witness is claimed.

`manifest.json` binds the selected heavy tuple, model, source and input vectors.
`dual.json` preserves the exact certificate; `audit.json` preserves the profile,
maps, rational residual and damage controls. The rebuilt matrix remains in
`experiments/scratch/g1-descent-best-independent-20261004`. All evidence is
separate from the broad cut inventory and from graph-5 matching diagnostics.
