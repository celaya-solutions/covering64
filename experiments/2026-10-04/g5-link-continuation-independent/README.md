```
Document:    Independent Fixed-g5 Descent Continuation Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      64ed007f4a3eecb45f1043727ccea77302d3d4a7a11c16833637c6cd7ef50f56
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Fixed-g5 descent continuation audit

The preparation gate independently checks the fixed-g5 rows, all 255 entries from
the prior checked cache, their registry classifications and primal vectors, and
all 128 initial two-edge neighbors (88 accepted and 40 rejected). Duplicate and
damaged mapping controls are rejected. The source was repaired before launch so
an exact fractional result can stop and save its actual record even when the
numerical status is not OPTIMAL; the earlier source is preserved in ignored scratch.

The bounded run completed five full neighborhoods: 88, 88, 93, 105 and 105 accepted
states. It made 465 fresh LP calls and used 14 cached results. Every evaluated
result reported OPTIMAL. The independently checked numerical trajectory was
11.500690015970484 -> 9.533204639679104 -> 9.448398722490406 ->
8.818415543401665 -> 8.152937802508724. The fifth neighborhood gave no improvement;
its smallest independently recounted residual was 8.279923931332881.

Solver time was 61.726965584093705 seconds and wall time was 68.66431654104963 seconds.
The readback reconstructs every neighborhood and registry decision, recounts the
saved vectors, checks cache origins and rebuilds the final cache. This is a numerical
local comparison in the specified registry-filtered fixed-g5 neighborhood, not an
exact local-optimum theorem or a global covering bound. No fractional completion or
integer cover was found. No optimizers are called by these audit scripts.
