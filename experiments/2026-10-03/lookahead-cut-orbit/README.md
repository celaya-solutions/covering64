```text
Document:    Heavy-Cut Separation Across Template Relabelings
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      600eb7a7792c01e5782090f12d8d212b6d8b90e3b4223011b9999a1ddcf72066
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Scope and result

The checked heavy-pattern inequality can be pulled back through every relabeling
that permutes the four anchor/hub groups and permutes the three anchor points
within each group. There are `24 * 6^4 = 31,104` such maps. These maps preserve
all template incidences, degree 20, the ordinary block universe, and the set of
all six permitted hub graphs. Every transformed inequality is therefore necessary
for a complete cover in the same conditional family.

The checker enumerates all maps, validates their anchor/hub structure, and directly
checks that eleven group generators preserve all 276 heavy and 1,200 ordinary
blocks. It saves the worst map and its full pulled-back coefficient vector.
A violation rules out only completion of the candidate's fixed heavy tuple in
this family. Passing the screen does not imply completion is possible.

For the old ten-hole tuple, 19 maps violate the bound. Scores range from 98144 to
156905, with threshold 108686. This shows why a single labeled inequality can
miss a relabeled copy of an already excluded tuple. The orbit screen retains the
same worst deficit, 10542, as the original certificate.

Version 1.1 captures witness and coefficient bytes once and binds hashes to those
exact inputs. A separate review identified a read/hash race in version 1.0; the
frozen baseline is unaffected. Its original checker is preserved in ignored
`scratch/lookahead-cut-orbit-v1.0.0/check.py`. Both original and new baseline
receipts remain available. Native candidates must also be frozen before review.
