```
Document:    Surviving Hub Graphs and Next Seed Scope
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      323822b142ce0651bc1e58b382898318c1f8ead318dc9e2f7002f3aab8fd8984
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

The 115 saved nearest/margin tuples contain **no registry-open doubled-matching
graph**. Matching graph indices are 0, 2 and 5; cycle indices are 1, 3 and 4.
All indices refer to the lexicographically enumerated six-graph list.

The lone mask-10 tuple is **nearest-master step 078**, with broad all-graph
elastic objective **11.673687648708288**. It retains cycles 1 and 3:

- Graph 1: cycle-061, cycle-061, cycle-089, cycle-030.
- Graph 3: cycle-086, cycle-086, cycle-101, cycle-123.

Graph 3 has excess vector (1,0,1,1,0,1) on hub pairs
(4,8), (4,12), (4,16), (8,12), (8,16), (12,16). It is a four-cycle, not a
doubled matching. Its exact tuple IDs and all six class lists are preserved in
`saved-screen.json`. No fixed-graph LP was run for step 078.

Nearest step 038 remains the lowest broad-score registry survivor among the
sampled labeled tuples. Its fixed-graph-1 score is separately verified as
8.024244815488677. The immediate useful change is to preserve graph-specific
registry eligibility during nearby-tuple descent. Simply choosing a lower
broad score can return to already excluded links, as happened for the prior
5.575882992498541 tuple. No sampled tuple is an exact feasible LP point or a
covering witness.

One-point hub transfers can leave the regular four-hub family, but the observed
transfer enters the previously studied sole-degree-19 branch and retains the
forbidden fifth heavy triple and relabeled 60-block core. That observation
does not exclude the broader nonregular branch. It does not presently offer
a stronger practical lead than the registry-filtered cycle descent.

This assessment used only saved results and exact relabelings. The single
separate step-038 graph-1 elastic diagnostic was the only additional solve.
No further optimization or whole-tuple isomorphism search was performed.
