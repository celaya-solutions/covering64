```text
Document:    Independent Audit of Heavy Link Blossom Inequalities
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      7fa3c5b67c1e0112d279a28d4c376c796a1702b53bc3c76879e611c543f582ff
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Scope and result

The blossom rows are necessary only for integer normalized regular full
four-sevenfold covers. For each anchor group, the heavy link has degree 2 at
its own hub and degree 1 at each of the other twelve outside vertices. An odd
degree sum on a vertex subset forces an odd positive boundary count, yielding
`2*x(E(S)) <= b(S)-1`. Complementary subsets give equivalent rows because total
degree is 14. The rows do not require the auxiliary double-triple variables.

`check_model.py` independently enumerates all 8,192 subsets for each of four
groups. It verifies complement selection and every omitted tautology, then
reconstructs all 8,096 retained rows in each case. All prior proto fields stay
unchanged and no variables are added. Ten damaged models per case are rejected.
`check_scope.py` rejects 16 invalid scopes without mutation.

# Screen and prepared CP pilots

The screen from `../../scratch/four-seven-link-lp-blossoms` contains 158
previously surviving representatives. Its two new positive certificates were
replayed by the separate raw checker and exclude only their restricted models:

| Representative | Exactly checked positive gap |
| --- | ---: |
| matching-038 | 8413/1000000 |
| matching-051 | 1007/200000 |

The other 156 returned numerical OPTIMAL status. Together with the earlier
100 checked exclusions, this leaves 102 restricted exclusions and 156 open
first-link cases. The entire four-sevenfold branch remains unresolved.
`blossom-screen-audit.json` records the exact replay. `screen-composition-audit.json`
confirms the screen bases equal the independently audited combined bases.

`check_prepared_cp.py` validates the v1.1.0 archive with pilots matching-029,
matching-113, cycle-069 and cycle-046. It checks all frozen source hashes,
300-second budgets, two workers per case, at most two simultaneous cases,
exact concatenation of independently audited facet and blossom rows, and
exactly seven fixed-link rows per pilot. `prepared-cp-v1.1-audit.json` passed.
This is an encoding audit, not a solver result. The older v1.0.0 preparation
included matching-038 and was superseded without launch.

# Evidence and replay

The blossom helper snapshot and models are in
`../../scratch/four-seven-blossom-cuts-v1.0.0`. The prepared replacement pilots
are in `../../scratch/four-seven-blossom-cp-v1.1.0`.
Hashes are recorded in each audit report. Run the three checker scripts in
this directory with `uv run python`: `check_model.py`, `check_scope.py`, and
`check_prepared_cp.py`. The latter checks preparation only and never solves.
