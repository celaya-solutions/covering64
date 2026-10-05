```text
Document:    Certified 61-Block Fixed-Link Runs
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-05
SHA256:      82e8f3711d5ea704f2740d46dedd74aa132806bda2596040242a8b7d13ca480d
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Certified reruns (in progress)

`run_case.py` rebuilds each fixed-link CNF with the encoder copied verbatim
from the probe, writes it as DIMACS, solves it with Lingeling through PySAT while
recording a DRAT proof, and checks the proof with drat-trim (commit
`2e3b2dc0ecf938addbd779d42877b6ed69d9a985`, built locally). PySAT's CaDiCaL
proofs fail drat-trim even on a small pigeonhole test, while Lingeling,
Glucose 4 and MapleChrono proofs verify, so Lingeling is used here.

The runs started on 2026-10-05 at 09:27 MDT with the header line
`SHA256: [pending]`; the saved script differs only by its filled header. Each
writes `solve.json`, `case.cnf`, `case.drat` and `drat-trim.log` under
`experiments/scratch/lb61/certified-<class>/`. Results will be recorded here
when all four finish. A claim needs `s VERIFIED` for all four.
