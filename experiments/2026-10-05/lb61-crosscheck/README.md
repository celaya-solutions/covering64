```text
Document:    Independent CP-SAT Cross-Check of the 61-Block Case
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-05
SHA256:      a08e700502af0d2e5e5f906a7f3189e64d151b2fe53af23def9d9b49bc2c4bd0
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent cross-check (in progress)

`cpsat_check.py` states the same four fixed-link problems directly as linear
constraints in CP-SAT, written separately from the CNF encoder: exact link
blocks at point 1, every triple covered once or twice, every pair covered
5 + [pair in E] times, and one or four doubled triples per pair. The runs
started on 2026-10-05 at 10:42 MDT (3 workers, 3,600-second limit each); the
saved script differs only by its filled header line. A CP-SAT INFEASIBLE answer
is supporting evidence, not a certificate. Results will be recorded here.
