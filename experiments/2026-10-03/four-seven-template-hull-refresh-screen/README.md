```text
Document:    Refreshed Matching-Only Template-Hull Screen
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      3d2dcd31e02fea9cf56eda741a1642efc45ccc0548ef4d4ce89e5a98ac82898c
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Refreshed matching-only LP screen

This campaign uses the independently audited 106-exclusion catalog: 12,690
matching templates per group, 55,528 continuous variables in `[0,1]`, and 4,550
rows. It first solves the whole matching branch, then all 50 still-open
matching first-link representatives. Every case receives at most 15 requested
solver seconds in total, shared between feasibility and optional phase I.
The maximum campaign allocation is 765 solver seconds; model construction,
preflight, integer certificate arithmetic, and evidence writing are outside
that solver-time budget. Actual solver durations are recorded.

The immutable refreshed matrix has SHA-256
`ee2072837ae28bcce599c60975995a5c88b3fc3eb635352abc089b3eb6d78bab`.
Its independent catalog/matrix audit is
`../four-seven-template-hull-refresh/independent-audit.json`, SHA-256
`af1c3224050faa086859930489e3bbce8fa5d9acaa922c6769f1c1bce528911b`.
The input manifest, complete surviving orbit set, proof union, audit, and
source utilities are hash-bound at load. No original-100 survivor count is
used to select this screen.

## Layouts and preflight

The whole-branch feasibility model is exactly the refreshed matrix. Its phase-I
model follows the earlier whole-hull pilot: all 4,270 original rows stay hard;
only the 280 template extension equalities receive 560 nonnegative unbounded
slacks with unit objective coefficients. Any resulting certificate is checked
against the original unsoftened matrix.

Each first-link feasibility model adds exactly seven explicit `x_block=1`
equalities, for 4,557 rows. It reuses the previously checked fixed-row reset
implementation. Its phase I softens only those seven equalities, using 14
nonnegative unbounded slacks; all 4,550 refreshed matrix rows remain hard.
Original variable bounds and global lexicographic block ordering are unchanged.

The independent no-solve preflight checks all four layouts. It compares every
original coefficient and bound against the refreshed JSON matrix, then checks
byte-identical canonical rows and original protobuf cores after removing only
the justified slacks/fixes. It inspects every unit box, objective field, variable
order/type, slack bound/sign/objective, and model dimension. It exercises all
50 selected first links in both fixed layouts: 100 fixed/reset transitions.
It rejects 46 damaged controls, including changed matrix coefficients/bounds,
boxes, objectives/types, row/variable counts, slack fields, stale fixes and
invalid fixed IDs. Reapplying a fix without reset is rejected for every case.
No Solve call occurs in preflight.

- Runner SHA-256: `de142bf735832c0d23d17c5acce8e5bb65ebb9c67e4215317a440db337d23930`.
- Preflight checker SHA-256: `4b246f999e467ecf39e520d0af284a9962877cc08a9de02aa70dfd5523451302`.
- Preflight result SHA-256: `f86bf29796b49445dd829d773200f35407bdeebeadf966dd59bcea1a3e4f3fb8`.
- Frozen fixed/reset source SHA-256: `c8841227df38eec07b28f9776e812e1df4c8c4175e80c0feead9fb15f8289b9e`.

Root supplied the passing catalog audit and authorized launch after the new
preflight passed. The run is sequential.

```sh
uv run python experiments/2026-10-03/four-seven-template-hull-refresh-screen/run.py \
  --output experiments/scratch/four-seven-template-hull-refresh-screen-20261003 \
  --preflight experiments/2026-10-03/four-seven-template-hull-refresh-screen/preflight.json \
  --seconds 15 \
  > experiments/2026-10-03/four-seven-template-hull-refresh-screen/run.log 2>&1
```

Every case preserves its exact fixed rows (empty for the whole branch), native
solver logs, timings, model/reset audits, sparse lossless primal, and any dual
or integer certificate attempts. Frozen sources, model protobufs, the complete
matrix, input hashes, source revision, solver version and command remain in the
new scratch output. Existing catalog names and prior results were not changed.

## Interpretation and readback

Positive certificates are pending until independent exact replay. A checked
whole-branch contradiction would apply to the regular matching branch; a
checked fixed-link contradiction applies only to that first-link type.
Neither alone proves an unrestricted covering-number lower bound. Numerical
feasibility is not an exact witness, and timeouts/UNKNOWN remain inconclusive.
Any near-integral block selection must pass both the package verifier and the
separate standalone covering checker.

`check_results.py` verifies all 51 saved records, exact model hashes, selected
first links, fixed/reset states and remaining phase-I budgets. It reuses the
frozen independent primal checker, which computes every row residual using
exact arithmetic on stored binary values. Its damaged controls cover malformed
and duplicate sparse entries, nonfinite values, incorrect widths, damaged
fixed blocks and stale reset coefficients. This is numerical readback, not
certificate replay; the latter remains separate.
