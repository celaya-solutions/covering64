```text
Document:    Fixed-Link SAT Runs for the 61-Block Case
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-05
SHA256:      0529d9c8f41e37dd05ee12927b65ccb9b112d1d762f61fcbc05eb7b617cfabf8
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Fixed-link SAT runs: preliminary evidence that 61 blocks are impossible

By `docs/lower-bound-61-structure.md`, a 61-block cover has a point a of degree
19 whose partner is the unique degree-20 point z, and a's link is one of four
classified minimum C(15,4,2) covers with z as its center. Relabel so that a = 1
and the link equals one of the four representatives in
`experiments/2026-10-03/link-classification/` (center 2 = z). What remains is
which four of the points 3..16 are the other partners of z and the perfect
matching of pairs with multiplicity six on the other ten points; the CNF
leaves both as variables.

`run.py.txt` is the exact script that was run (byte-identical to the probe
`lb61_link.py.txt`, SHA256
`14b9876fe620fc557961b0e0a4d000f014f4db8cf2d7075067cdefd2d9cbd596`). Each case has
144,553 variables and 512,424 clauses. With a 150-million-conflict budget,
CaDiCaL 1.9.5 (through PySAT) returned UNSAT for all four classes:

| Link class | Result | Time | Conflicts |
|---|---|---:|---:|
| shape-1 | UNSAT | 1,095 s | 3,860,179 |
| shape-4 | UNSAT | 1,255 s | 4,215,300 |
| shape-44 | UNSAT | 1,045 s | 3,502,843 |
| shape-47 | UNSAT | 1,169 s | 3,835,768 |

The logs are saved beside this note. These runs produced no proof, so the
result is **not certified**: see `../lb61-certified/` (DRAT proofs checked by
drat-trim) and `../lb61-crosscheck/` (an independent CP-SAT formulation).
