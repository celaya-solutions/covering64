```
Document:    Independent Two-Swap V2 Pre-Run Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      993d0ab6aa7dd62e974712a555998a1ea2a3d80489f0ce43bf76e692d32645be
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Frozen pre-run audit

The independent gate passed before the sole v2 production pass. Its immutable
`gate.json` SHA256 is
`77c9f3fa9eccfb89229be8d9a09bdc4e26e64a0a296b19af44179473059a9a64`.
It binds producer manifest
`0f006df5844a67bf5595378e8dc156890a117ecab613b5e2ead9f74b463d9287`,
the production binary, source and input bytes, independent control sources,
compiler, finite expectations, and separately reviewed pruning proof.

The finite control run checked every one of 6,885 supported masks and 139,776
mask-to-block entries against independent combinations. It compared 31 fixed
63-block partial states and 60 fixed 64-block final states, including 230,000
subset counters and 130,769 completion comparisons. Pair metrics, actual final
ranks, rollback, and 29 invalid operations agreed. The initial family and every
partial and final family were checked by both cover verifiers at their actual
cardinalities: 92 families in all. Five damaged input families were rejected.

Recorder controls checked 30 ordinal positions, nine shell-prefix counts,
and a real D34-to-D29 exchange encoded only in explicitly synthetic logs.
Empty improving-tie lists passed for zero-control, partial-timeout, and complete
metadata fixtures; 14 malformed recorder fixtures were rejected. Synthetic
complete metadata is a recorder control, not an optimizer result.

The audit launched no optimizer. Its native executable only processed the fixed
finite controls. All raw control files remain in the ignored sibling scratch
folder, with hashes in the gate. `check.py` refuses to replace the existing gate
or finite-control binary; the gate is not intended to be rerun in place.

This v2 sibling preserves the original producer and independent draft folders.
The production native kernel is unchanged from the original producer; v2 fixes
recorder handling of empty improving ties and validates additional accounting
relations. The preserved original draft control header predates a formatting-only
brace edit; only the hash-bound v2 sources are authoritative for this gate.

The exact-distance-two proof is in
`../weak-pair-swap-scan-runtime-independent/LOCAL-REPAIR.md` and is bound by the
gate. Completion pruning follows pair floor five only; remaining legal rows
and rank are evaluated after the final incoming block is added. The shell
excludes distances zero and one. This audit grants no global lower bound.
