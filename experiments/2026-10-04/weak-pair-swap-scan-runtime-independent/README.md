```
Document:    Independent One-Swap Runtime Outcome
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      5399173ab39205fe841fe0c118e625149d674f7eb4bafed31cd253ff73f99059
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# One-swap runtime outcome

The pinned CP-final H12/D32 family had 275,456 distinct one-for-one replacements.
The frozen scan completed all of them. It reported 8,667 legal neighbors, 22
strictly better neighbors, three successive best records, and four final ties
with rank (12 holes, 29 summed pair-max deficit). No cover was found.

The independent receipt is `postcheck.json`, SHA256
`a491a5ae273d2eab20bff3c3992771ce130d3293236eee62d9c05c6214e1207c`.
All six distinct saved families were reconstructed from their swap identities,
recounted by direct subset inclusion, and checked with both covering verifiers.
All four best ties satisfy the pair floor, all single/quadruple rows, and all
four core caps. Each also has full-row stronger deficit 29.

The best ties all remove lexicographic block ID 881 and add one of IDs 1142,
1143, 1154, or 1359. The canonical representative is `swap-881-1142.txt`, SHA256
`44e0ee69fb32f37eed00955e25c699a72430d85871ca03a348c0bf572edb7a0a`.
This matches the producer's saved representative exactly.

The pre-run gate, manifest, source archive, runtime logs, recorded ordinal
positions, improvement order, tie set, and verifier receipts all passed.
The native elapsed time was 0.521694 seconds; overall process wall time is
recorded in the receipt. It is an observation, not a controlled speed benchmark.
No second enumeration or solver was launched by this audit.

Completeness is supported by the audited frozen nested loops, fixed 64/4,304
axes, exact terminal count, and normal exit. Unrecorded trial metrics were not
individually recomputed. The result concerns only this fixed-base one-swap
neighborhood under the declared legal filters. It proves no global lower bound.
