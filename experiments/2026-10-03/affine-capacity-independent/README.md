```text
Document:    Independent Affine Extension Capacity Bound
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      0c49c96cf50c83ee8247cde491a17e2ca509d6eaf59d0240e28581d28f9a1802
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Checked extension capacity bound

In the fixed pool of 48 circles and 240 affine line extensions, a 64-block
cover cannot use exactly 21 extensions. It would retain 43 circles and omit
five. Each omitted circle has ten triples, unique among the circles, so the
extensions must supply at least 50 circle-triple incidences.

For every five-circle set the checker computes all 240 extension scores.
An extension scores one for each removed circle with which it shares three
points. Exactly one extension from each of the 20 lines is first required to
cover the collinear triples. The maximum total incidence for 21 extensions is
the sum of the largest score in each line plus the largest remaining score.
This is an upper bound on useful coverage: it can count repeated coverage of
the same triple more than once.

All 1,712,304 five-circle sets were enumerated, with no pair screening or
symmetry reduction. The maximum capacity is 46, below the required 50. The
complete capacity histogram is recorded in `audit.json`. A separate agent's
GF(4) implementation reached the same exclusion after a safe pair screen;
its smaller screened universe has maximum 45, so these maxima refer to
different sets.

The runner independently compares 300 native results with direct set
intersections and sorting in Python. Ten damaged inputs and queries are
rejected. Source, binary, input, compiler and pool hashes or versions are
recorded. This bound is limited to exactly 21 extensions in this one-circle-
family pool. It is not a global lower bound or a covering witness.
