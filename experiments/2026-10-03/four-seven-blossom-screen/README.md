```text
Document:    Certified Odd-Set First-Link Screen
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      2a061ac57bcf6eeab44a5486d70b6f9d7bb89be1c2b2b6c918af207e0c22ed13
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Two new independently checked exclusions

The first-link screen added all 8,096 nontrivial heavy-link odd-set inequalities
to the lifted models with the first five feature rules and thirteen additional
facet families. Every one of the 158 previously open cases was tested with a
ten-second per-stage LP budget. Two matching cases have positive exact
infeasibility certificates:

| Case | Exact positive certificate gap |
| --- | ---: |
| matching-038 | 8413 / 1000000 |
| matching-051 | 1007 / 200000 |

The separate raw checker replayed both certificates and checked all 158 result
records, selected-case coverage, source hashes, model hashes, row arrays and
fixed block IDs. These add to the original 100 exclusions. Totals are 27 cycle
and 75 matching exclusions, with 102 cycle and 54 matching cases still open.
The remaining 156 cases have only numerical LP feasibility; none is a covering.

The compact evidence archive contains every result and the complete two exact
certificate weight vectors. Raw models and source snapshots remain in ignored
scratch and are listed by hash in the artifact manifest. Preserve those files.
The next input catalog removes exactly these two checked cases. This is an
integer-cover exclusion within the regular four-sevenfold branch, not a global
lower bound for C(16,5,3).
