```text
Document:    Bounded Maximum-Margin Heavy Master Pilot
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      ac5385b3314232048de6dc09c1b890df40cc13fd25e33b3ac886bb8e154c2fc6
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Maximum-margin pilot across new heavy patterns

The authorized pilot completed 20 candidates, adding 20 exact necessary cuts.
It used 62.47577795665711 combined solver seconds and 65.53973270906135 wall
seconds. All master statuses were FEASIBLE, so maximum margin was not proved.
No candidate improved the existing elastic objective 5.575882992498541. The best
new candidate, case 014, had elastic residual 18.723394713737736 and achieved
normalized margin 8.686659. No checked fractional completion or cover was found.

Independent readback found 22–28 replacements relative to the old best tuple,
confirming that this pilot reached new regions. In these 20 samples, a large
margin inside the known cut halfspaces did not predict a small true completion
residual. A margin is a search proxy, not a negative elastic cost or a hole count.

## Formulation and bounds

The model retains the unchanged 605 structural heavy rows and replaces separate
hard-cut rows with 333 normalized margin rows. It has 276 heavy Boolean variables
and one integer margin variable Z. Each row is `heavy_dot - Z >= rhs` in common
units of 1,000,000; Z is nonnegative and is maximized. Setting Z=0 exactly recovers
all known necessary cut inequalities, so the heavy projection is unchanged.
There is no incumbent-distance objective or hard distance restriction.

For any selection of exactly 28 heavy blocks, a cut's heavy dot product is at
most the sum of its 28 largest coefficients. The minimum of these per-cut
margin upper bounds is the safe initial bound 141,507,155. It is recomputed as
new cuts are added. All 333 initial certificate row weights satisfy |weight|≤D,
and every new rounded certificate is checked against that norm before use.
The initial protobuf therefore has 277 variables and 938 constraints.

The same frozen 697-row ordinary-completion basis and fresh one-second GLOP
elastic solver are reused. Numerical primals and duals are saved. Exact signed
row combinations at denominator 1,000,000 supply new cuts; apparent zero
residual would trigger an exact rational primal check and stop the run.

Caps were 20 candidates, three seconds per master, one second per LP, 80 combined
solver seconds, and 100 wall seconds, with one worker and base seed 2026104064.
The separate execution receipt binds the actual launch revision
`5d4d2b252037b965ef6834908dc825a6d79fd391`; the original preparation revision remains
accurate in the unchanged manifest. No solver call occurred during preparation.

## Checks and saved evidence

The focused independent gate rebuilt the exact 277-variable/938-row initial
protobuf, all normalized cuts, the objective and safe bounds, and rejected three
damaged controls. Its postcheck then independently replayed all 20 incremental
models, achieved margins, numerical LP vectors, and exact signed certificates.
The receipts are in `../margin-heavy-master-independent/`. `integrity.json`
adds a fresh check of every manifest input and raw artifact hash.

`manifest.json` pins preparation, `execution-receipt.json` binds launch,
and `result.json` records every case. Full model snapshots, solver parameters,
responses and logs, completion rows, numerical primal/dual vectors and exact
learned cuts remain in ignored `experiments/scratch/margin-heavy-master-20261004/`.
The previous nearest-master source and evidence were not changed.

The separate stitch reporter found zero accepted LP-score improvements, so
`stitched/checks.json` has zero new 64-block candidates. This pilot ran once;
no further optimizer was started automatically. The current cut inventory is
353 necessary cuts within the same fixed-anchor regular four-sevenfold family.
There is no unrestricted lower-bound claim or new covering witness.

- `run.py` SHA256: `d04c60c256ee9299aff701dd2b930a0965a365106d423bb21afa3b2633b70058`
- `manifest.json` SHA256: `a0e1dbc4173627632ea721a1407304c9b23b879e5b1e7bef40d5ffb9143bef0d`
- `execution-receipt.json` SHA256: `7caf060e0a4e6f37a59dedf7a229ef4a630ca839e55928b9cedbd026dbf5e3bf`
- `result.json` SHA256: `d8a08f414b6401f7386ba95049144c2e63d550e4b04b6ba03022bff87c4feb10`
- `integrity.json` SHA256: `639e38743de7ceec9b5e06e0de20b2fda9f8e56a684456b24a0b0dff5b75c295`
- `stitch-input.json` SHA256: `0f28bc8e04b0f51b78364026e60ed2f3aa668c56587da7bc7830d4b4acf3db38`
- `stitched/checks.json` SHA256: `066c42fd07ead52e4b9e4011bdc034895a95c9bf85438341c36738e204c4c5a5`
