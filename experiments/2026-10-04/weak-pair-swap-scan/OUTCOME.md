```text
Document:    Weak Pair One Swap Producer Outcome
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      b9c13d542cd0568a76c639c57e618848b34c9605ca35e7fffeb7f84fc620a61c
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Completed producer outcome

Root executed the single frozen seedless one-block scan. It completed normally
with exit zero in 0.521694 native seconds (0.8760813340777531 wrapper seconds).
The 135-second watchdog did not fire; there was no relaunch or budget transfer.
All 275,456 unique replacements were evaluated, and 8,667 passed the frozen
pair floor, single/quad rows, and four named core caps. The exhaustive local
best rank is `(12,29)`, improved from `(12,32)`. No 64-block cover was found.

There were 22 legal neighbors strictly better than the starting rank and three
strict best-so-far records: removing block 881 and adding 421 gave `(12,31)`;
adding 601 gave `(12,30)`; adding 1142 gave `(12,29)`. All block IDs here are
zero-based positions in the complete lexicographic five-subset universe.

Four final best ties replace block 881 by 1142, 1143, 1154, or 1359. Each has
64 distinct blocks, 12 uncovered triples, per-pair maximum deficit sum 29,
expanded stronger-row deficit sum 29, minimum pair count 5, zero single and
quad deficits, and core overlaps `[1,1,1,2]`. Every distinct saved family has
an independently recounted metric record, full family hash, package verifier
receipt, and standalone parser/verifier receipt in the ignored candidate audit.
The representative additionally passed the standalone CLI.

The chosen representative SHA256 is
`44e0ee69fb32f37eed00955e25c699a72430d85871ca03a348c0bf572edb7a0a`.
The independent runtime postcheck passed, SHA256
`a491a5ae273d2eab20bff3c3992771ce130d3293236eee62d9c05c6214e1207c`.
The producer result SHA256 is
`183e01fc06bfffefb869b932439398e1bacc1075b33e9d8e07d7dec7aaf654ad`.
The full candidate audit SHA256 is
`a135bef956c6bef61b33894f46441e3d6bc6a3486496a156b2830a6f2865e1ef`.

This proves the best rank only in the pinned initial family's legal one-swap
neighborhood under the documented named rows. It gives no global lower bound
or general nonexistence conclusion. Existing frozen sources, inputs, README,
manifest, and gate were preserved; this supplement records only the outcome.
