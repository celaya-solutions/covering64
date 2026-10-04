```
Document:    Independent Affine Norm Circle Construction and Pool Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      461e9b325ecb5474e3a31e51fe8cd2d4bf51070e781910c5c41c01841ea3efc5
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent construction

Use GF(4) with w squared equal to w+1. The anisotropic form Q(u,v)=u squared + uv + w times v squared has only the zero vector as a zero. Its three nonzero level sets around each of 16 centers give 48 distinct five-point circles. The 20 affine lines have four points each. Adding point 17 to each line gives another 20 five-point blocks. Direct counting checks that these 68 blocks cover every one of the 680 triples on 17 points exactly once.

The point map into the separate GF(16) construction uses embedded GF(4) values [0,1,6,7] and theta=2: label(u,v)=(embed(u) XOR (embed(v) shifted left once))+1. This permits exact comparison while the independent constructor itself uses only GF(4) multiplication and the displayed norm.

Deleting point 17 leaves the 48 circles and 20 four-point lines. Extending each line by any of its 12 external points gives 240 distinct five-point blocks. Together with the circles these form the 288-block pool. Its 80 collinear triples each occur in 12 candidates, and its 480 other triples each occur in four. The independently built PGL pool, all plane blocks, lines, circles and support lists agree exactly.

# Model gate

The independent checker reconstructs all 288 Boolean variables in global lexicographic block order, the exact64 cardinality row and all 560 coverage rows. It rejects eight damaged models. No symmetry, point-degree profile or circle/extension split is imposed. A covering witness still needs both package and standalone verification. This pool is a construction restriction, not a complete search of the full 4,368-block universe.
