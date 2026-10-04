```text
Document:    Independent Six-Hole Release Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      ad6227ec15ec6c98dd7159fd56a2126d70087171742ba6c7a6fd64a2d09024db
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent six-hole release audit

The preparation gate passed before the producer ran either case. The auditor
made no optimizer calls. The producer was authorized to run each frozen case
once, with 120 seconds, four workers, and seed 2026104101.

The adaptive pool is reconstructed from the ten-seed 277-block union and every
carrier of the 12 distinct holes in four independently checked six-hole states.
Those carriers contain 720 blocks, and their union with the prior pool contains
952 blocks. The comparison case contains every one of the 4,368 block variables.
All 64 slots are free; no distance cap or additional overlap bound is present.

Both full protobufs, all 4,948 hint values, and the complete parameter messages
were reconstructed independently. Each model has 1,166 rows. They retain the
two existing core-overlap bounds of 59 and the two proved five-heavy partition
rules. Both directions of every threshold indicator were checked. The prior
exhaustive threshold tables were replayed for 79 local counts and 243 categories
per partition. The full-pool membership row is the empty linear equality 0 = 0.

The objective is `65 * holes + original_core_overlap`. Because any overlap lies
between 0 and 60, the extra term only chooses among states with the same number
of holes. The complete hint has six holes, original-core overlap 59, and objective
449. Nine damaged model controls were rejected.

`postcheck.py` checks every saved strict improvement and the native final
responses separately. It reconstructs all assignment bits and checks every
active row, then runs the package verifier and the separate standalone verifier
on every state. Final equal-objective families are retained even when they differ
from the callback's last saved family. Every state is scanned for all disjoint
five-heavy partitions, beyond the two partitions constrained by the models.

The result audit passed. Both cases returned FEASIBLE with six holes,
original-core overlap 59, composite objective 449, and numerical bound 0.
Neither improved the hint's objective. The adaptive call used 120.029447209
wall seconds; the full call used 120.029846334 wall seconds.

Each callback saved only the common starting hint. Both native final responses
were different equal-score families: the adaptive final shares 62 blocks with
the hint, and the full final shares 60. All four saved/final records (three
distinct families) passed both verifiers as validly formed 64-block noncovers
with exactly six missing triples. No five-heavy obstruction was found in any
family. The adaptive final has four heavy triples with counts 6, 7, 7, 7;
the full final has four, each with count 7.

Seven damaged native responses were rejected. Both verifiers also rejected
three malformed witness controls: an out-of-range point, a repeated block,
and a missing block. No optimizer was called by either independent checker.

These are bounded construction attempts. A numerical status or bound is not an
independently checked lower-bound theorem. UNKNOWN is inconclusive. Raw model,
parameter, solver response, log, and launch files stay in the ignored scratch
folder and are bound by SHA256 in the gate and result audit.
