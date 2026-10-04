```
Document:    Stronger Compact Pair-Two-Triple Count Model Run Outcome
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      21e3a9cbf8397905a4b99fe62a02357268fc5660da15eb4fe929a8c693bc3e07
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Stronger compact count-model run outcome

The sole 120-second run ended `UNKNOWN`. It found no feasible assignment:
there were zero callbacks and no final solution vector. No first-feasible time
exists for this run. The independent postcheck passed the native response and
all source, model, input, parameter, and raw artifact bindings.

The result is inconclusive. It is not an infeasibility proof, a covering witness,
or a new bound on the covering number. No retry or budget extension ran.

| Run fact | Value |
| --- | --- |
| Start (UTC) | 2026-10-04T12:33:06.620626+00:00 |
| Source revision | `b8b941cff21345cd4aca840f9ec3b974d004b823` |
| OR-Tools | 9.15.6755 |
| Planned and used budget | 120 seconds, four workers, seed 2026104301 |
| Optimizer calls | 1 |
| Status | UNKNOWN |
| Elapsed solve | 120.01586362498347 seconds |
| Native wall time | 120.01130300000001 seconds |
| Objective bound | 0 |
| Feasible incumbent | None |
| Saved callbacks / final assignments | 0 / 0 |
| First feasible callback time | None |

## Incomplete guidance and native stages

The six-hole guidance remained block-only and intentionally infeasible. No hint,
model row, or parameter changed after the independent gate. The native log reports
`The solution hint is incomplete: 4368 out of 5608 non fixed variables hinted.`
After presolve it reports 5183 of 6423 nonfixed variables hinted. These are native
reported hint stages, not evidence that the hint became feasible.

Presolve begins at 0.01 seconds and search begins at 0.96 seconds, a roughly
0.95-second presolve/setup interval. The presolved model has 6,423 variables and
15,219 constraints. There is no native first-solution message. These timings
come from one run and make no general performance claim. Any comparison with
the earlier DP runs must distinguish the lack of a feasible starting assignment
here from their complete feasible hints.

## Evidence

| Artifact | SHA256 |
| --- | --- |
| Result | `f14c20d0d19ae955fcbb636097f45a928cc376639b2a2cc7216a57c67c78e88a` |
| Independent postcheck | `6fe45a64156f3abc09a76030d1543fdfa79b8711a7cf76801dab7b2cd9d0c5b4` |
| Independent launch gate | `6a641ed9bf2e6d8163d6bf931f49fafad38010a2b37a20649d5b3ef2569d3abc` |
| Frozen model | `2901bb03bc1b12a9ab950bf93b1e3bd0ef84760ab9ce87ce8fc0bb6b59d45d87` |
| Frozen runner | `0445dff332c3e8b817c843ea3d82c56f1b95b85ec7918213af6dc14ab99e6803` |

`result.json` binds all eleven raw files under ignored
`experiments/scratch/compact-pair-two-counts-run-20261004/`: model, parameters,
used parameters, manifest, gate, preparation source, runner source, start
metadata, native response, solver log, and stdout. Their hashes were freshly
rechecked for this outcome. The outer launch log is `run-stdout.log`.
`outcome-files.json` adds this report, the result, independent postcheck, and raw
files to a separate hash index. Preparation sources, documents, and indexes
remain unchanged historical records.
