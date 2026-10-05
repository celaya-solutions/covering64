```text
Document:    Independent Check of Circulant LP-Certified Trees
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      935a3c82c1a6549d2deeb148d30e98be02bc58fe087ebb38ee5b21bc1f883c75
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent tree check

`check.py` replays saved trees with plain integers and no producer or solver
import. It recomputes each node's residual demands and open blocks, requires
each branch node's candidate list to be exactly the open blocks through its row
in block order, regenerates every child, and checks support deficits and exact
Farkas margins at the leaves. In full mode every saved node must be reached
once from the root and the run must be complete.

Pilot mode checks chosen root subtrees of an incomplete run. For profile 0 it
verifies the complete first two subtrees of root row (1,2,3): 106 branch nodes,
39 support leaves and 1,279 Farkas leaves, then 85, 48 and 1,086. Thus no cover
with this profile contains the first root candidate, and none contains the
second while omitting the first. Changed multipliers, dropped candidates and
missing child records are rejected. `review.json` records the result.
