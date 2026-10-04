```
Document:    Global Five-Heavy DP Run Outcome
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      1253611a1ea3d286aadb9218d81af7d4736ff579b191e192f68f42e8536c3751
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Global five-heavy DP run outcome

The single authorized run finished `FEASIBLE` with the unchanged 10-hole hint.
It found no improvement, zero-hole state, or covering witness. The independent
postcheck passed for both saved states and all four covering-verifier calls.
The preparation `README.md` and `runner.md` remain unchanged historical records.

## Run facts

| Item | Observed value |
| --- | --- |
| Start (UTC) | 2026-10-04T11:28:02.183511+00:00 |
| Source revision at start | `fdd62792a1f4696075da2002bc71747c10ba2dcf` |
| OR-Tools | 9.15.6755 |
| Budget | 120 seconds, four workers, seed 2026104104 |
| Optimizer calls | 1 |
| Status | FEASIBLE |
| Elapsed solve | 120.02173283300363 seconds |
| Solver wall time | 120.01857600000001 seconds |
| Saved callbacks | 1, at 2.013563 seconds |
| Best and final objective | 651 = 65 × 10 holes + 1 original-core overlap |
| Objective bound | 0 |
| Core overlaps | [1, 8, 55] |
| Maximum global five-heavy partition weight | 24 |
| Final identity | Same 64 block IDs as the callback and original hint |

The logged presolve starts at 0.02 seconds and search starts at 2.06 seconds,
a roughly 2.04-second presolve/setup interval. The presolved model has 12,340
variables and 109,810 constraints, compared with 10,488 variables and 103,345
rows before presolve. The native response records 60,404 conflicts, 4,518,081
branches, and deterministic time 517.31264177994967. These are observations from
one run, not a general speed or performance claim.

## Artifact index

All paths below are relative to this folder unless prefixed with `experiments/`.
The result binds the 14 raw runtime files by path and SHA256. Their hashes were
rechecked when this outcome record was written. `outcome-files.json` adds a
separate index for this outcome, both candidates, the postcheck, its verifier
receipts, and the raw runtime evidence.

| Artifact | Path |
| --- | --- |
| Authoritative result and runtime hash index | `result.json` |
| Callback near-cover | `full-4368/callback-000-h10-c1.txt` |
| Final near-cover | `full-4368/final-response-h10-c1.txt` |
| Outer launch stdout | `run-stdout.log` |
| Frozen preparation manifest | `manifest.json` |
| Preparation and runner records | `README.md`, `runner.md`, `files.json`, `runner-files.json`, `runner-preflight.json` |
| Independent pre-run gate | `../global-five-heavy-dp-independent/gate.json` |
| Independent postcheck | `../global-five-heavy-dp-independent/postcheck.json` |
| Outcome artifact hash index | `outcome-files.json` |
| Runtime evidence directory | `experiments/scratch/global-five-heavy-dp-run-20261004/` |

The ignored runtime directory preserves the exact model, parameters, used
parameters, manifest, gate, preparation source, runner source, start metadata,
solver log, stdout, native response, callback records, and complete callback and
final variable vectors. The large model and scratch artifacts stay outside Git.

| Binding | SHA256 |
| --- | --- |
| Result | `2d7070dfc4101cd3c060bdfd221d6bdbcac5ba3d96eb6fbd0d0f66f2ca05c49c` |
| Independent postcheck | `27cfe94ea4370651888bd664fc7484aa33a46ab8def40214883e08cd55048da5` |
| Callback and final candidate files | `011fcce3b4568a211a357c2e0a608a8f5f5b8cb801ace1c324024fc35a670adc` |
| Frozen model | `ee2570107d996ee8f69a0118b11abbad91320f5b19eb6e196ef6a34367d5d295` |
| Frozen parameters | `e55795cc6169e2cd321e10fdd040f2b22f6a08da3eeac711c7d8edde2ff54d6d` |
| Preparation manifest | `d01230c07cb5b1226d2fcc95912586ac5ff07723da4e170be5e908167eeb9f5b` |
| Preparation source | `477e8e03630185c233bbd61e8a12d9b4361cb45e271ad4bdfecdf875a635e24e` |
| Execution source | `34753fb6b1a12027a10f76aacd8f69c43a293471ce3578eec3917995d56fe0ed` |
| Independent pre-run gate | `47b9fed1ee3d9315f0f7b1bf56d87c85e8798d46305375bce8a371e80da6cbfa` |

## Interpretation and scope

The model retains every lexicographic block variable and adds a conditional
necessary filter for valid 64-block covers. That filter can remove near-covers.
This bounded optimization result supplies no unrestricted lower bound and does
not settle whether a 64-block cover exists. A timeout is inconclusive, and even
a native CP-SAT `INFEASIBLE` response would not be an independently checked theorem.
No additional optimizer was run or authorized.

The independent postcheck passed for both saved states, their full variable
vectors, all active constraints, thresholds, domains, frozen bindings, native
response, and actual global partition maxima. It ran the package and standalone
cover verifiers on each state: all four calls confirmed the 10-hole near-covers.
It rejected three damaged assignments: a selected block, a global threshold, and
a fifteen-point bound. Both states have minimum point degree 19, minimum pair
count 4, and three pairs below 5. Neither state is a covering witness.

The preliminary outcome saying postcheck pending is preserved under ignored
`experiments/scratch/global-five-heavy-dp-development-20261004/outcome-postcheck-pending/`.
