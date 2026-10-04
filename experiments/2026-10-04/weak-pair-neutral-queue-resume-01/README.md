```text
Document:    Resumed Strict-First Neutral Queue Campaign
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      dc51a025143f55cbc357213b42e91db6574f9dd1834e956ee013e738b15317b4
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Frozen resume preparation

This new campaign starts from the independently reconstructed pending frontier
of the completed first neutral campaign. It carries all 14 retained unscanned
families at rank (11 holes, D2max 25), including the previously popped designated
next family. It excludes all 20 historical and previously processed hashes.
There is no seed-revisit exception. The first campaign remains unchanged.

The new allowance is at most 32 centers and 64 shell calls. Each shell retains
its 120-second kernel budget, 135-second watchdog, and five-second termination
grace. A center runs its one-swap and two-swap shells sequentially. There are no
seeded random operations, restarts, budget transfers, or native recompilations.
Preparation runs no search. Root owns every production launch after an
independent hash-bound GO.

The kernels, capped neutral recorders, original strict validators, and bounded
shell wrapper are reused byte for byte. Their hashes and original source
archives remain bound through the inherited preparation. The prior result,
independent runtime receipt, reconstructed frontier, and raw-file index are
also bound. Preparation checks every prior raw-file hash and checks all 14
frontier families through both recorder paths and both real cover verifiers.
All are partial covers; verifier rejection of full coverage is expected.

The queue still prefers the best strict improvement across both complete
shells, then the full lexicographic block-ID tuple. Strict descent discards
worse-rank pending states. Without a strict move, all retained unseen equal-rank
states are added to the pending frontier. Completed and historical center
hashes are never revisited. The result explicitly saves the full remaining
frontier, including a popped designated next family, to support a later
bounded resume without losing pending work.

The runner stops for a cover, incomplete shell, empty retained frontier, or
32-center budget. An incomplete center is not a certified closure. Empty
retained frontier is not full plateau exhaustion: each shell's neutral
recorder can retain only its first 64 equal-rank families in traversal order.
Any actual cover still requires both verifiers. No global nonexistence claim
follows from this restricted search.

Eighteen synthetic queue controls cover strict preference, tie ordering,
frontier preservation, deduplication, historical exclusion, incomplete/cover
stops, the 32-center/64-shell cap, and seven invalid resume frontiers. Native
recording code is unchanged and retains its earlier independent audit.

Preparation: `uv run python experiments/2026-10-04/weak-pair-neutral-queue-resume-01/prepare.py`.
Production requires `run.py --gate PATH --gate-sha256 SHA --execute`; the runner
refuses any existing result or output folder and requires an independent GO.
