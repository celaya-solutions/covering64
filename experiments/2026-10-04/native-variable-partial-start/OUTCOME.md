```text
Document:    Variable Cardinality Partial Start Outcome
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      a496dc41191f4b9140219f211430f123dd17f9edc1011cdad8d0c7ae2d21f662
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Completed campaign

Both authorized 300-second native calls finished normally without a cover.
They ran sequentially with no relaunch or budget transfer. Root collected
campaign exit 0. Both native calls returned 1, passed every saved-family check,
and had empty stderr and no watchdog event. The best complete family remained
the separate pinned Belic 65.

| Seed | Start holes | Best raw/admissible exact 64 holes | Iterations | Mutations | Actual final size/holes |
|---|---:|---:|---:|---:|---|
|2026104801|9|9|39,293,091|58,324,686|64/18|
|2026104802|12|10|42,912,188|63,684,756|62/32|

Both report 300.001 native seconds, a live cardinality range 62–64, and exactly
four initial fallback selections. The zero-mutation initial records retain
both partial starts and the separate complete 65. The H9 call never improved
its initial family. The H12 call improved to H10, with four diagnostic core
overlaps `[1,0,1,0]`. The final live state is saved with its actual cardinality;
in the second call it is 62, not an exact 64 candidate.

The best H9 family remains
`15db6bdbf8c6210c6754cbe52a1408dda6a279429bb5471cf03a1b68b24f0c46`.
The best H10 family SHA256 is
`a8f2258c5a194307954bcaf11b6dfd186753841ba26ec5d1a52f9aa6852a6f07`.

No complete family of size at most 64 appeared. This finite heuristic campaign
does not establish a global lower bound or rule out a 64-block cover. The calls
partly overlapped the separate CP experiment, so wall time and iteration rates
are not controlled comparative performance measurements.

# Checks and frozen evidence

Producer wrap-up rechecked every saved family and log hash, compared final log
events with result metadata, and confirmed empty stderr. The runner checked
all initial, strict-improvement, and final families through both verifiers
using actual cardinalities. Initial raw/admissible records preserve the pinned
starting bytes, while the independent native outcome audit is recorded in
`native-variable-partial-start-independent/postcheck.json`.

Frozen manifest SHA256:
`d66e4f2dfe7604b06dcd9d94ac49efc0c82b748b03977195e4a3924f6b2daaa5`.
Gate SHA256:
`ea66aee6e55730dc8b0716e0472badc64cabed1b58468d25ba23293d9d8158d5`.
Result SHA256:
`24ff9d900ab7fa5c09fcc24810bedd80fe64eba530b00c6af995fdc593b00d59`.
Independent runtime postcheck SHA256:
`a6c83b3d60653d09c85650facc367534f94fbfe3aac1655c2125711aa0010920`.
No frozen source, input, control, binary, or manifest was changed during this
wrap-up. This supplement and its index add observations only.
