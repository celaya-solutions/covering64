```text
Document:    Bounded Nearest-Heavy Lazy Master Campaign
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      a00998814bbf693458107fb9b84135d2ae67faaaa53dd4e9c81d1b7942d063ac
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Bounded nearest-heavy lazy-master campaign

The single authorized campaign generated 95 heavy tuples and 95 new positive
exact signed-dual certificates. It used 177.71904825384263 combined solver
seconds and 188.37468745792285 wall seconds, then stopped at the reserved margin
for the 180-second solver budget. No tuple improved the baseline elastic
objective 5.575882992498541. The best new candidate scored 5.966796868079938;
the largest score was 14.103160141092703. No exact fractional completion or
covering witness was found.

Ten candidates replaced four of the 28 baseline heavy blocks; 85 replaced five.
CP-SAT reported OPTIMAL for 52 masters and FEASIBLE for 43. All 95 elastic LPs
reported numerical OPTIMAL, and each numerical dual yielded a positive exact
integer-arithmetic separation. The master statuses are solver results, not
independently checked theorems about nearest distance. The campaign did not
exhaust all tuples at any distance.

## Model and budgets

The previously audited heavy master is reused: 276 Boolean variables, exactly
28 heavy blocks, 52 outside-incidence equalities, and 552 nonanchor triple-cap
rows. The initial master adds 238 necessary completion cuts, giving 843 rows.
The cut list is the prior 124 checked cuts, 113 checked planes from the complete
LP neighborhood sweep, and the baseline-pattern cut with gap 5.425. All 238
cuts are distinct after exact positive-integer scaling normalization.

A soft objective minimizes `28 - baseline blocks selected`, half of full binary
Hamming distance. It adds no hard radius restriction and stays centered on the
same baseline throughout. Incumbent incidence is not imposed on an unrestricted
model: this entire experiment is explicitly the fixed-anchor regular degree-20
four-sevenfold branch, with the audited six hub residual graphs retained.

Each candidate has the same 697-row ordinary completion LP on 1,200 variables.
Only heavy contributions shift row bounds. A fresh one-worker GLOP instance
minimizes total L1 row slack, with a one-second limit. Both its numerical primal
and dual vectors are saved. Positive signed-row certificates are rounded at
denominator 1,000,000, checked exactly against the ordinary variable box, and
converted into new necessary heavy inequalities before the next master.

Caps were 100 candidates, two seconds per master, one second per LP, 180 combined
solver seconds, and 240 wall seconds, with one worker and base seed 2026104063.
Master seeds are the base plus case index. One worker and a fixed seed control
the search setup; time-limited execution is not claimed bitwise reproducible.
Numerical FEASIBLE masters can supply heuristic candidates without a nearest
claim. Missing candidates, unresolved LP/dual status, checked exact fractional
feasibility, or a budget reserve stop the run. No unresolved case occurred here.

## Checks and artifacts

The root's focused gate in `../nearest-heavy-master-independent/audit.json`
independently matched the entire initial protobuf, including the soft objective,
all 843 rows and 238 cut planes; it checked every manifest hash and two damaged
controls. The separate 113-plane audit in the complete-sweep independent folder
passed before this campaign launched. No optimizer ran during preparation.

`manifest.json` pins 239 input files and the initial model. `result.json` binds
765 raw artifacts: initial/source/gate snapshots, each incremental model,
parameters, solver response and log, completion rows, both numerical vectors,
and each learned cut. `integrity.json` freshly checks all input/raw hashes and
recorded statuses. The root independent postcheck passed: all 95 incremental masters, 95 numerical
primals, 66,215 shifted row bounds, and 95 exact signed cuts were replayed.
The receipt is `../nearest-heavy-master-independent/postcheck.json`.

`stitch-input.json` lists accepted LP-score improvements for the separate
64-block stitch reporter. There were none, so `stitched/checks.json` reports
zero new candidates. Existing five-hole and three-hole partial families remain
separate earlier evidence. The LP score must not be reported as a hole count.

Raw models, vectors, logs and proof artifacts are under ignored
`experiments/scratch/nearest-heavy-master-20261004/`. The source and completed
campaign were not edited or rerun after launch. No further optimization was
launched automatically.

This bounded negative result concerns the examined heavy patterns only. It is
not a global lower bound, an unrestricted exclusion, or a covering design.

- `run.py` SHA256: `723f38f97707931ac003e7b64feefe1d2f569bfda3aa8cd9a718b73f908bf251`
- `manifest.json` SHA256: `ceb818fbde0d776e504e0b9ec4f93f5d56229e026bc46d0d79f60d936296927a`
- `result.json` SHA256: `1dfc1ac5b1d2d9d2dceff0eb4f37dbf43a2f1588c1b4fa3e444586226b51a11d`
- `integrity.json` SHA256: `9ee49b169715872b61eb2f0a00b1ff448b734222df0cc20c8c1cc4713270bb98`
- `stitch-input.json` SHA256: `0f28bc8e04b0f51b78364026e60ed2f3aa668c56587da7bc7830d4b4acf3db38`
- `stitched/checks.json` SHA256: `066c42fd07ead52e4b9e4011bdc034895a95c9bf85438341c36738e204c4c5a5`
