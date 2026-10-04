```text
Document:    Constructive Affine Circle Deletion Capacity Search
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      114f0c62c04dccf87c84ba900623917729494e65831c26c2d535ab80917de098
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Purpose and scope

The six approved runs completed 230,827,708 proposals in 60 reported native
seconds and found no capacity survivor. This is an inconclusive heuristic
result; no exact extension-completion input or covering witness was produced.

| Deleted circles r | Best capacity found | Required capacity |
| --- | --- | --- |
| 9 | 84 | 90 |
| 10 | 93 | 100 |
| 11 | 102 | 110 |
| 12 | 111 | 120 |
| 13 | 120 | 130 |
| 14 | 129 | 140 |

This bounded heuristic searches for deletion sets in the original 48-circle
family whose extension incidence capacity is at least the necessary 10r.
It is a search for inputs to a later exact extension-completion model. Passing
capacity would not prove that even one valid 64-block cover exists; failure to
find a capacity survivor is also inconclusive.

The exact capacity function is the previously audited seven-bin integer count:
take the best extension of each of the 20 affine lines, then the r−4 largest
remaining extension weights. An extension's weight is the number of deleted
circles whose triple it covers. This maximizes total circle incidence using
16+r extensions and at least one per line, while allowing duplicate coverage
of the same triple. A deleted set of size r needs 10r distinct triple incidences.

Circle 0 remains deleted throughout, using the separately checked affine
transitivity certificate. All circle IDs refer to the lexicographically sorted
original (1,2) family. Blocks still use point labels 1–16.

## Frozen search policy

A proposal exchanges one deleted circle other than circle 0 with one retained
circle. The score is capacity minus 10r. Improving and equal proposals are
accepted. A worsening proposal with capacity change delta is accepted when a
uniform random draw is below exp(delta/T).

Temperature is T=0.15+3.5*(1−phase)², where phase runs from zero toward one
over 50,000 proposals. The state restarts from a random deletion set after each
50,000 proposals. All random choices use mt19937_64 with the saved seed.
The best scored proposal is saved even if it is rejected by the annealing rule.
Up to eight capacity survivors would be retained, each differing from earlier
survivors in at least four circle-membership bits. Reaching eight would end a
run early; otherwise its wall-clock budget ends it.

The approved schedule uses r=9,10,11,12,13,14 in that order, one native thread
at a time, ten seconds per case. Seeds are 2026103991–2026103996 respectively.
The pilot does not explore r=15–24 and does not repeat the CP relaxation.

## Validation and evidence

Warning-clean release and ASan/UBSan builds each pass:

- 1,000 independent geometric capacity-oracle comparisons.
- 16,000 swaps and 16,000 exact state-and-score rollback checks.
- 48 damaged-state, seven malformed-model, seven malformed-argument, and
  five malformed-query controls.
- One 0.02-second smoke run with independent readback of its best candidate.

During search, state membership is checked every 1,024 proposals and at the end.
The Python runner independently recalculates every saved best and survivor
capacity from explicit circle/extension intersections. It checks distinct circle
membership, cardinality, circle 0, survivor distance, and acceptance counters.
No covering witness is claimed from a deletion set.

`check_results.py` checks the six saved runs against their native output and
source/binary/gate hashes, recalculates the saved capacities, and rejects seven
damaged result controls per run. Individual JSON results and the aggregate
`readback.json` are authoritative for the completed proposal counts and scores.

- Native source SHA256: `893ee64ef8ced52c13a0d2f5793982f7346e6fd74d6bbeb8f4824ee2aecc38d2`.
- Release binary SHA256: `4bd48a810e1890c06e88b09d8d5dc73ea36c0908e513f722fe57ea196d94dfce`.
- Capacity matrix SHA256: `e42529770438fb51629d885f58eb1b11a36f82c2a17bd94795b3defab810f3fd`.

Raw binaries, source snapshots, controls, and native run outputs remain outside
Git in `experiments/scratch/affine-capacity-annealer-20261003/`. The final gate
supersedes a preliminary preflight receipt after a Python string was line-wrapped
for Ruff; the earlier receipt and Python snapshot are retained in the raw folder.
The native source and release binary did not change. Neither preflight is a
substantive search pilot.

`check_point_stars.py` then checks all 16 deletion sets consisting of the 15
circles through one point. Each has exact capacity 138 at E=31 extensions,
below the required 150. Python geometry and native counts agree. These are
only 16 specified sets, not an enumeration of all 15-circle deletions. The saved
heuristic best sets for r=9–13 share a point; the r=14 set has maximum point
incidence 13 and no common point. The observed score pattern is not a bound.

A possible future reduction must keep the extension count E fixed: every
k-subset K of an actual deleted set receives at least 10k circle incidences
from its chosen E extensions. Thus the maximum possible capacity U_E(K) is at
least 10k for every such K. An exhaustive universal maximum below 10k at the
same E would exclude all larger deletion sets. The existing k=8, E=24 maximum
75 cannot be applied directly to E=25: a further extension can add up to six,
giving only the upper bound 81, which does not exclude the required 80.
No additional enumeration or annealing was run for this observation.

To read back completed work, run
`uv run python experiments/2026-10-03/affine-capacity-annealer/check_results.py`.
Fresh pilots require separate output directories: the runner refuses to
overwrite a completed case. Wall-clock termination can change the final proposal
count across machines even with the same seed; sources, exact counts, and all
saved candidate masks are preserved.
