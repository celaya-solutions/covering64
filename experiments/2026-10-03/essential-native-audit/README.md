```
Document:    Independent audit of point-essential native SAT encoding
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      50caf34ce178eba9b91eb37134bfc297436ab137234d2c534cfec8a284b822cd
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent native SAT audit

No defect was found in the audited point-essential encoding. `result.json` stamps both reviewed source files; exact source snapshots remain under `experiments/scratch/essential-native-independent-audit-20261003/`.

The private flag gates an at-most-one counter when true and an at-least-two counter when false. Explicit coverage clauses exclude zero incidence. Together these enforce the exact equivalence between the flag and multiplicity one. Each selected block-point incidence requires a private flag for a triple through that point in the same block. Unselected blocks impose no such condition.

`check.py` independently enumerates all 1,024 families of triples on five points, covering pairs. There are 388 full covers, of which 10 satisfy point-essentiality. SAT results under every complete block assignment match the direct oracle. A separately constructed CP model enumerates exactly the same 10 essential full covers. The flag-only portion also matches all 388 full covers; all 3,880 attempts to force one private flag to its opposite value are rejected.

A tracked counter wrapper checks every generated auxiliary ID. For the actual 16-point regular model, there are 4,368 public block variables, 560 private flags and 128,240 counter variables, ending at ID 133,168. All counter variables lie strictly above the private flags and their allocation ranges are disjoint. Both counter directions are checked on every triple.

The audit independently reconstructs all native bounds in the regular branch: exactly 64 selected blocks, degree 20 for every point, the safe degree lower bounds and pair incidence at least five. Its clauses contain all triple coverage constraints and only the stated first-block normalization. The public block order remains lexicographic. In 128 deterministic relabeling trials, the chosen block maps to 1,2,3,4,5 and all point, pair and triple multiplicities are preserved.

These checks validate the implementation and the scope of the regular branch. They do not prove a 64-block cover exists or does not exist; the branch is complete only jointly with the degree-19 cases. The review did not modify either search source. Ruff passes for the audit script.

Run from the worktree root:

```sh
uv run python experiments/2026-10-03/essential-native-audit/check.py
```
