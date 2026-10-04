```
Document:    Single Cut-Guided Cycle Pilot and Full Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      80fd3018469d97f02c6f5a7d4882f552fb0e7c2f9c9c5aa0f29f11ca7c4ff516
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Single cut-guided cycle pilot

The one authorized pilot used native version v1.3.0, seed 2026104722, one process
and a 300-second native budget, starting from the audited ten-hole performance
state. The optional labeled-cut guide was enabled. Inputs, source, binary,
compiler metadata and gates were snapshotted before launch under ignored scratch.
The wrapper completed in 300.401014 seconds with no forced termination and empty
stderr. Exit one is the native program's normal result when no cover was found.

The best raw and full-score states are byte-identical. They retain ten uncovered
triples, with base score 82 and full score 82. The labeled cut has left-hand side
118449, above its threshold 108686, so the added penalty is zero. The independent
lookahead recount finds 680 admissible ordinary blocks and no unsupported triple.
The run made 81057018 proposals and 190 actual cache evictions. This is not a cover.

The full saved-state audit passed for all 45 states and 16 recorded moves. Every
state was checked by the independent incidence oracle and both covering verifiers.
All cut metrics, complete lookahead sets, best records and rollback were checked;
ten altered metric controls were rejected. The checker and every frozen artifact
are bound in audit.json and files.json.

Root subsequently checked all 31104 family automorphisms against this best heavy
tuple. None violated the previous cut: the minimum left-hand side was 116376 and
the maximum was 158119. This says only that the tuple passes that orbit of necessary
inequalities; it does not establish the existence of a completion. The separate
orbit receipt is ../lookahead-cut-orbit/cut-pilot-best-audit.json.

Raw search output, every saved state and all verifier outputs remain in ignored
experiments/scratch/four-seven-template-cut-pilot-v1.0.0. Compact best states,
source runner, checker, manifest and receipts are preserved here. No repeat run
was performed. No first-link registry or global covering bound was changed.
