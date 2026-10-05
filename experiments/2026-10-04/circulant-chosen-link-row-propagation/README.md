```
Document:    Bounded Propagation of the Chosen Circulant Link Survivors
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      43ead9cb48ba50a52ecc1fd3ab2ce94afe5f99d043f1ac21afee589773ae52e5
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

This stage prepares and benchmarks iterative exact row-bound propagation
only for the 10228 survivors of the frozen full single pass. It does not
launch a full iterative pass, an optimizer, or failed-literal probing. The
complete survivor list and terminal result are hash-pinned before loading.
The source and benchmark sample are frozen before propagation begins.

For every case, retain all 3003 point-one-avoiding pentads as initially free
binary variables. Rebuild the 455 exact outside triple residuals, then append
the exact sum of 44 remaining blocks. No removals from the earlier pass are
silently inherited. Starting with empty selected and removed sets, scan rows
in order. If selected count equals demand, set all unassigned row variables
to zero. If selected plus unassigned count equals demand, set all unassigned
row variables to one. Too many selected variables or too little remaining
support gives an explicit contradiction. Repeat complete scans until a
contradiction or a scan with no new assignment.

Each force record names its row, value, and every newly assigned global
block ID. Final contradictions save the exact demand and selected/free
support. Final selected and removed bitsets are hashed as 376 little-endian
bytes, with local bit i denoting global five-block ID 1365+i. The complete
state is reconstructible from the saved trace. A fixed point without a
contradiction is only a survivor, not proof of feasibility. If propagation
does determine 44 remaining blocks satisfying every row, combine them with
the pinned twenty blocks and require both cover verifiers before saving
an actual 64-block witness.

The authorized benchmark takes survivor indices floor(i*10228/1000), for
i=0..999. Its cooperative ten-second wall budget includes loading and
output; no new case starts at or beyond 9.75 seconds, and every row visit
also checks that deadline. If interrupted within a case, save the valid
forcing prefix and its next row while leaving that case incomplete. Save
the exact next benchmark position. No retry or continuation is automatic.

Prepare with `uv run python experiments/2026-10-04/circulant-chosen-link-row-propagation/run.py prepare`.
After the manifest is frozen, replace `prepare` with `benchmark` for the
single authorized 1000-case measurement. Full iterative production has no
entrypoint and requires separate root review and authorization.

All benchmark traces are stored as a compressed JSON-lines file in ignored
scratch. The tracked receipt pins that file, records operation counts and
outcomes, and reports actual wall-budget compliance. Runtime extrapolation
from the sample is explicitly an estimate. Any exclusion concerns one exact
profile and one exact chosen-witness image, never all affine constructions
or unrestricted 64-block existence.
