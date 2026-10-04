```text
Document:    Fully Cut First-Link Integer Pilot
Version:     v1.2.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      36c335a961c4facb7a7c69cfa68829dd4e8001458d937d3339bf789acd724325
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Completed experiment

Four integer searches were run from the normalized regular full
64-block branch. Each base includes the auxiliary double-triple lift,
the original five feature-rule families, the thirteen later feature facets,
and all 8,096 heavy-link blossom rows. Each pilot then adds exactly seven
selected block equalities fixing one first-heavy-link representative. There
is no objective, hint, or fixed pattern for another link or the double flags.

| Representative | Seed | Seconds | Workers | Variables | Rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| matching-029 | 2026103301 | 300 | 2 | 4,768 | 12,421 |
| matching-113 | 2026103302 | 300 | 2 | 4,768 | 12,421 |
| cycle-069 | 2026103303 | 300 | 2 | 4,768 | 12,397 |
| cycle-046 | 2026103304 | 300 | 2 | 4,768 | 12,397 |

Three cases have large observed blossom violations in the saved fractional
solutions. The fourth, `cycle-069`, has the lowest block fractional mass in
that inspection and an earlier inconclusive 60-second integer pilot. The
original `matching-038` was replaced before launch because the new blossom
LP screen produced a positive certificate, pending independent replay. This
selection does not promise that these are easier integer cases. The batch launcher permits at most two simultaneous
processes, giving at most four CP workers. Each seed is a CP-SAT run seed;
worker-specific seeds are managed internally by the solver.

# Frozen preparation and audit

The archive is `experiments/scratch/four-seven-blossom-cp-v1.1.0`. It holds
all model-building source snapshots, both proof manifests, frozen selected
input records, both fully cut base models, four fixed-link models, all solver
parameters, source revisions, versions, and hashes. Preparation and search
are separate commands. Preparation does not invoke a solver.

`check_model.py` parses raw protobufs without importing builders. It confirms
that each cut base preserves every field of the original lifted base, all
new cuts reference only the original block variables, and each pilot adds
only the seven correct first-link fixes. It also verifies model dimensions,
source/model/parameter hashes, seeds, budgets, and the absence of objectives
and hints. All four prepared models passed. The checker does not itself
certify the validity of the added cuts; separate cut audits cover that claim.

The final preservation checker passed after a line-wrap style fix and rehash.
Ruff passed for the runner and checker. Solver parameter parsing was checked
without launching a search. The earlier v1.0.0 preparation remains frozen
and was never launched; the case replacement uses a separate v1.1.0 archive.

# Running and interpreting

After independent clearance of the blossoms and combined pilot models:

```sh
uv run python experiments/scratch/four-seven-blossom-cp-v1.1.0/run.py \
  batch experiments/scratch/four-seven-blossom-cp-v1.1.0
```

Each solve preserves its full log and response protobuf. Any extracted
integer candidate is checked by both the frozen package verifier and the
separate frozen `check_cover.py`; the full outputs and hashes are saved.
Candidates are marked as covers only when both verifiers agree and exactly
64 distinct blocks are present. With no integer solution, verification is
recorded as not applicable.

`UNKNOWN` or a timeout is inconclusive. `INFEASIBLE` alone would be a solver
result for one fixed first-link case, not an independently checked theorem.
These four cases do not exhaust the branch or the unrestricted covering
problem. All four pilots returned UNKNOWN after approximately300 seconds each. No
integer candidate was supplied, so both covering-verifier outcomes are
recorded as not applicable. The total solver time was1200.030617 seconds.
No cover or new exclusion follows. `result.json` summarizes each case;
`pilot.json.gz` preserves source snapshots, metadata, complete solver logs,
response protobufs, outcomes, and artifact hashes. The independent combined
model audit passed before launch.
