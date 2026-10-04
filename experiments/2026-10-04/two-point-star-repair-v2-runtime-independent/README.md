```
Document:    Independent Two-Point-Star V2 Runtime Outcome
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      7f4e5d9654314da7ff29dda76072f7254c2d42d798996d0a2f2bf8a66f55174f
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Checked star-repair outcomes

Both fixed star runs completed with FEASIBLE status, objective 12 holes, and
reported bound zero. Their solver wall times were 60.006325000000004 and
60.006730000000005 seconds. No cover or hole improvement was found. These
bounded outcomes are inconclusive about either neighborhood's optimum.

The independent `postcheck.json` SHA256 is
`d6f35f60be4bb2090018ddaec0036e6a8305823e132faf5dd40e9a337621675a`.
All four saved callback/final assignments were checked, yielding three distinct
families: the starting H12/D26 family and two new H12/D29 families, each differing
from D26 by three removed and three added blocks. Both new families have pair
floor five, zero single/quadruple deficits, and satisfy all four named core caps.
These are fresh diagnostics; only the pair floor was imposed in the models.

The new family hashes are
`52d6a7990b959385f15dadaf61b02cda787aa035d4738abeeb316e8f3cc5a4d5` and
`1019a357d0a6b31e4b41132d3ea90efad3a32381ecc864a34a74db096ebf85b9`.
Their complete canonical witnesses are preserved here, together with the
independently reconstructed starting family.

The audit verifies source, gate, model, and raw-file bindings; actual recorded
60-second/four-worker solver parameters and fixed seeds; every saved Boolean
assignment; exact-64 cardinality; all frozen outside-star memberships; pair
floor five; and every hole indicator by direct triple inclusion. Each witness
passed both covering verifiers. The solver response, reported objective/bound,
final vector, callback sequence, covering labels, and stop rules agree with
saved records. Neither run fired the watchdog, and no search was rerun by this
audit.

These are two fixed neighborhoods centered on the same frozen D26 family.
Their solver statuses and bounds are local reports, not independently checked
proofs. The outcomes establish no global lower bound, unrestricted infeasibility,
or new covering design.
