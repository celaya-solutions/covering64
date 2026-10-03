```
Document:    Independent Selected Heavy Hub Model Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      e0751e67ddf189f56addbca4a409180ebbe964271d17f2f0ebe37aaa0d7fa92f
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent selected-heavy hub model audit

The frozen selected-heavy h9 model passes this independent audit. It extends
the previously audited normalized-hub model by exactly 52 Boolean variables
and 280 constraints, for totals of 6,480 variables and 7,534 constraints.
Removing the added variables, rows, and hint suffix restores the entire prior
protobuf exactly, including tables, objective, and all other fields.

The selected triples are (1,2,3), (5,11,16), (7,10,13), and (8,9,14). For each
selected triple T and outside point p, let q count blocks containing T∪{p}.
The new flag is exactly equivalent to μ(T)≥6 and q≥2. The reconstruction checks
both directions, requires q≤3 when T is heavy and q≤2 when T is sevenfold,
and permits at most one repeated hub per selected triple.

Each point-packing row contains every heavy-anchor flag at that point, together
with the selected hub flags there. Its sum is at most one. In particular, an
unselected heavy triple can still prevent a selected hub from occupying one of
its anchors. Hub roles for unselected triples are not encoded, so the model
must not be described as imposing all heavy-hub constraints.

All 6,480 saved hint values are independently derived from raw block containment,
including the preexisting block, hole, local-family, residual, and heavy flags.
Every domain and all 7,534 constraints are evaluated without a solver. The only
active new hub flags correspond to root hub 4 and outside hubs 12 and 15.
The h9 witness hash agrees with the separately audited seed.

A 208-case truth table checks the local reification and multiplicity caps.
Eleven negative controls reject altered thresholds, polarity, caps, packing,
missing rows, removal of an unselected heavy-anchor term, and corrupted hub
hints. The independent checker imports only frozen independent row utilities;
it does not call the production cut helper as an oracle. Saved source files
are hash-checked as provenance evidence.

Run from the worktree root:

```sh
uv run python experiments/2026-10-03/selected-heavy-hubs-independent/check.py
```

Model SHA256: `63d5960c2cd4881c7f58f587170913f7ba1fd49c060f500f44ac29d03345a7a9`.
The large model remains in ignored scratch at `selected-heavy-hubs-h9-20261003`.
This validates a conditional partial-construction model and one saved feasible
hint. It is not a full cover, an unrestricted encoding audit, or a nonexistence
proof. The unchanged h9 local families retain their separate 25>24 completion
obstruction until at least one local family changes.
