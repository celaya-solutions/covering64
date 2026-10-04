```
Document:    Prepared Soft Strong-Pair Four-Core Model
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      af5b47d320e9585c1da64217641e413096e6b97dcb2d16ed3356359ad468acc1
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Prepared soft stronger-pair model with four core caps

Status: PREPARED, NOT RUN. Preparation made zero optimizer calls. A separate
independent gate and root authorization are required before the sole planned
120-second, four-worker run with seed2026104302.

The previous hard stronger-pair model returned UNKNOWN without a feasible
assignment. This sibling starts with a complete feasible H49 assignment and
minimizes necessary-cut deficit before holes.

## Model and preservation

Keep all4,368 lexicographic block Booleans, exact cardinality64,120 pair counts
with domain[5,64],560 triple counts[0,64],560 exact hole flags, all1,680
single-triple necessary cuts, and the three prior core caps. Append the
independently checked fourth transported-core cap at55. There are no degree20,
symmetry, family, incumbent-incidence, or global-profile restrictions.

Add120 integer d_P in[0,128]. For each pair P and every two distinct outside
positions a,b, impose

    3*c(P)-c(P+a)-c(P+b)+d_P >=12.

There are10,920 such rows. The exact required minimum d_P is the positive
largest-two deficit. Since pair count>=5 and triple counts<=64, every required
deficit is at most12-15+64+64=125, so the bound128 cannot exclude a family
satisfying the unchanged constraints. A true cover has d_P=0 by the independently
audited stronger-cut proof, so this soft formulation preserves every64-block
cover passing the already proved necessary constraints. No global lower bound
or independently checked nonexistence theorem follows from this experiment.

The objective is561*sum(d_P)+holes, with no core tie-break. One integer unit
of sum(d) dominates any change among all560 possible holes. Solver d variables
may contain slack; the actual D2max/D2sum are always recounted from blocks.
A solver objective value is not substituted for actual D2 metrics.

Total:5,728 variables and14,405 rows. The row breakdown is1 cardinality +680
count equations +1,120 exact-hole reifications +1,680 single-triple cuts
+10,920 soft stronger cuts +4 core caps. Nonnegativity/domain bounds are
variable domains rather than extra rows.

## Complete feasible H49 hint

Candidate SHA256:
`a7feb783eb9f36e710feba5356857514cde146104b95de03fa47716126afd9c4`.
Every one of5,728 variables has one hint entry, including all zero block values.
Exact raw subset recount gives49 holes, D2max74, D2sum170, D3=D4=0, minimum
pair count5, and four core overlaps[0,2,2,4]. Each hinted d_P is its actual
largest-two deficit. The complete hinted objective is561*74+49=41,563.

Both independent covering-verifier paths agree that this family has49 holes;
it is a feasible soft-model assignment, not a covering witness or a feasible
hard-D2 hint. Every actual serialized row, enforcement literal, variable domain,
and objective was evaluated on the complete hint. Frozen read-back repeats this
check and confirms all unique indices0..5727 exactly once.

## Gated runner

`execute.py` requires --execute, a gate path, and its expected SHA256. The
independent JSON gate must have passed=true, decision=GO, and exact bindings
for manifest_sha256, model_sha256, parameters_sha256, hint_sha256, and
runner_sha256. Every current frozen source and model/parameter/hint artifact
is hash-checked before the solver is reached. The run refuses existing outputs.

The runner saves every delivered callback without an objective or tie filter,
plus a separate final vector whenever the solver has a feasible final solution.
Each saved state has raw block and full-vector files, canonical minimum deficits,
all-row validation, raw subset metrics, four-core and global-profile diagnostics,
and both covering-verifier reports. It stops when the *actual recounted* D2max
is zero and the other required checks pass. Such a state is a qualified hard-D2
hint; only zero holes with both verifier passes is a covering witness.

Raw logs, callback stream, response, sources, values, witnesses and model stay
in Git-ignored scratch directories. The result includes hashes of every raw
runtime file, source and gate bindings, elapsed and solver time, first feasible
time, callbacks, bound, status and actual qualification. UNKNOWN is inconclusive.

## Frozen artifacts

- model: `experiments/scratch/soft-strong-pair-four-core-20261004/model.pbtxt`, SHA256 `7fddd41609b304a391c88d75237824cd4e79bcd5b2153f252b2324d00be06926`.
- parameters: `experiments/scratch/soft-strong-pair-four-core-20261004/parameters.pbtxt`, SHA256 `fc0b2caa47a74a6de8867f024d9b4e37288c5e1858c327814eaa0c7946c70a63`.
- hint: `experiments/scratch/soft-strong-pair-four-core-20261004/complete-h49-hint.json`, SHA256 `372ad68a6bfd6fa184e23040b1816fca04365ef54f71bc50c667859e322e202d`.
- Manifest SHA256: `27f6839e030bd2ba7e940847282cc619e786151316d1b657ac471cef8e77b231`.

`manifest.json` records the source revision, Python/OR-Tools versions, source
hashes, audited proof bindings, budget, domains, objective, hint metrics, and
all four core ID lists. `preparation.json` records the successful row/vector
check and the hint's global-profile diagnostic. Source body hashes and all
frozen file hashes were rechecked. Ruff passed. No optimizer was invoked.
