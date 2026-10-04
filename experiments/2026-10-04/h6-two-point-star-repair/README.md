```
Document:    H6 Two-Point Star Repair Pilot
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      bbb8af13d9bfe55a4099bb5c71f619b96d7b1428f2b66617873e0e5005bc9595
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Prepared local repair

This prepares one 120-second CP-SAT call with four workers and seed 2026106001.
The parent owns launch after independent review. Preparation calls no optimizer.
The wall-clock watchdog is 140 seconds, with five seconds to terminate before
forced kill. There is one call, no retry, and no budget transfer.

The checked input is the H6 raw64 family from native seed 2026105901, SHA256
`2d018ffa5e3e424193a4197b23891b52fa59b7ca411d06108e0ab1666bb85855`.
The actual source HEAD at preparation is
`d2bfd843889e8b6f549881c7493fae196383b170`; hashes pin uncommitted preparation
files as well as dependencies. Large model files stay in ignored scratch space.

All 4,368 block variables retain global lexicographic ordering and 1-based labels.
Every membership outside the two-point star {6,10} is fixed: 2,002 blocks,
including 30 selected. The 2,366 free blocks rebuild 34 selected blocks. The model
has exact cardinality 64, 560 exact hole flags (both implications), all 120 pair
floors 5, H<=6, and objective minimize H. It has 4,928 variables and 1,242 rows.
There are no D2, D3, D4, core, degree-profile, or rotational restrictions.

The complete initial hint is **infeasible**. It has 64 selected blocks and six
exact holes, and satisfies all domains and every row except pair floors
(4,6), (5,6), and (10,12), whose counts are 4. `initial-hint-audit.json` records
their exact row indices, activities, domains, and both cover-checker receipts.
This is an infeasible hint; no feasible-start assertion is made.

The old `two-point-star-repair-v2/run.py` stays byte-for-byte unchanged. This pilot
imports its builder and tightens only the final hole cap from 12 to 6. It directly
reuses its atomic JSON persistence, family formatting, two cover verifiers, full
vector checker, model reader, and callback persistence class. A new one-call
runner uses frozen parameter text, a gate bound to the manifest, pinned source
and dependency hashes, an exclusive child-start marker, and the same subprocess
terminate/kill watchdog pattern. Every saved assignment must pass all model
domains and active rows, then both cover verifiers. H=0 alone is insufficient.

`controls.py` checks the rejected initial vector, a control relaxed on exactly
its three failed pair rows, damaged vectors, hole equivalence directions, frozen
parameters, gate damage, mocked watchdog paths, repeated-launch rejection,
mocked UNKNOWN response persistence, and callback replay. It never calls a real
optimizer. The mock callback deliberately contains the infeasible initial vector
and is rejected on replay; it is not a candidate.

Scope is one fixed neighborhood. UNKNOWN or a watchdog timeout is inconclusive.
CP-SAT INFEASIBLE is not an independently checked theorem. No result here proves
unrestricted nonexistence or novelty. The prior v2 runtime audit and H6 finite
pair diagnostic are pinned as provenance; they do not certify this new model.

Preparation: `uv run python experiments/2026-10-04/h6-two-point-star-repair/run.py --prepare`.
Controls: `uv run python experiments/2026-10-04/h6-two-point-star-repair/controls.py`.
The parent alone may execute `run.py --execute PATH_TO_INDEPENDENT_GO_GATE`.
