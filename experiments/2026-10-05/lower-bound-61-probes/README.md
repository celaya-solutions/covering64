```text
Document:    Exploratory Probes of the 61-Block Case
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-05
SHA256:      9c0f57cd3b7ae8b468649ae50e52face565acecadd814acb1974d60d1855d7bf
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Exploratory probes of the 61-block case

These scripts test how hard the forced 61-block structure of
`docs/lower-bound-61-structure.md` is for standard tools. They are kept
verbatim as text (`*.py.txt`) because they were run once from scratch space; no
claim depends on them. E is placed as star center 16 with leaves 11-15 and
matching (1,2), (3,4), (5,6), (7,8), (9,10).

| Probe | Result |
|---|---|
| `lb61_lp` LP relaxation with doubled-triple variables | feasible (0.2 s) |
| `lb61_cp` CP-SAT, 12 workers, symmetry level 4, 600 s | UNKNOWN, 649 conflicts |
| `lb61_dive` greedy LP dives, 8 runs | LP infeasible only after 11 fixed blocks |
| `lb61_sat2` compact SAT encoding, CaDiCaL 1.9.5 | 136,768 vars, 490,520 clauses; open after about 14 minutes |
| `lb61_case` X_z fixed at random (two cases) | open after 3,000,000 conflicts each |
| `lb61_link` one A-point link fixed to each of the four classes, E variable | open after 3,000,000 conflicts each |
| `lb61_link_lp` same as LP with E fractional | feasible for all four classes |
| `lz_enum` z-link enumeration for five random X_z (Python, 240 s) | no link found in 0.4-0.95 million nodes; incomplete |

An earlier encoding with totalizer pair constraints reached 16.8 million clauses
and was abandoned. The counter used in `lb61_sat2` was checked against all 64
assignments of six inputs for thresholds one to three with no mismatch.
