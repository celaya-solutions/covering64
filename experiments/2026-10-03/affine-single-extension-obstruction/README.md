```text
Document:    Affine Single-Extension Counting Obstruction
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      05ace7e19947aa869b57ac0c16860a1e53636609c2bf373e1096e1700b9f1745
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Restricted counting result

Within the fixed pool of 48 finite circles, if exactly one extension of each of
the 20 affine lines is chosen, at least 47 circles must remain. Thus this
subcase needs at least 67 blocks. This does not bound the full 288-block pool,
the six-family 528-block pool, or the unrestricted covering problem.

Each circle is a five-point cap. Its ten pairs determine ten distinct secant
lines. Every extension of a line can cover at most one of the circle's ten
triples; it does so exactly when the line is secant and its added point belongs
to the circle. If that circle is removed, its ten triples have no other circle
covering them. Consequently all ten secant lines must choose an added point
from the removed circle.

For two removed circles and any shared secant line, its added point would have
to lie in the intersection of both circles and outside that line. The checker
enumerates all 1,128 pairs and records at least one shared secant line for each
pair where this set is empty. Therefore no two circles may both be removed.
All labels are 1-based; only internal certificate array indices are 0-based.

The checker independently validates the pair design, the 480 circle triples,
the 80 line triples, cap intersections, and every circle/line/extension triple
count. It rejects seven damaged pools. Its full finite obstruction list is in
`audit.json`; the earlier GF(4) norm construction supplies the frozen pool.

This argument uses exactly one extension per line. With additional extensions,
a circle can make up a missed secant contribution elsewhere. The conflicting
line list alone does not prove an analogous bound for those broader cases.
