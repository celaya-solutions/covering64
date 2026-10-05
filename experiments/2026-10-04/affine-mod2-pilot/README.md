```text
Document:    Residual Parity Certificate Pilot
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      de1637428de4f825040fb1f6acfa1af39bdbbadb268a031fd3bcb1a372a2ad15
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Saved finite pilot

The pilot checks 1,096 original propagation survivors and 25 new-catalog sample survivors. It reconstructs all 3,003 point-avoiding pentads and removes only columns touching a zero-demand triple. Exact residual triple equations and the sum of 44 blocks are reduced modulo two. Each contradiction stores the subset of rows whose XOR has zero eligible coefficients and odd right-hand side. No optimizer or propagated-domain assumption is used.

All 1,121 cases completed in 3.113935 seconds. There are 484 original and 21 sample parity contradictions; 612 original and four sample cases remain consistent over GF(2). Consistency over a finite field does not imply a cover. The separate audit in `affine-mod2-independent` checks all 505 certificates and independently rechecks all 616 consistency claims with column-space elimination. Sixteen damaged controls are rejected. Review SHA256 is `abfc1ee5faa0b1ec34f827d1f7f1fbcee287de6137c4a32ebcc89d5f46fae607`.

The exact executed source is archived verbatim as `executed-source.txt`, matching the manifest and result source hash. The current `run.py` only formats one long string and fills the document hash; it has not been rerun. This preserves the original pending header and long line as historical source data without rewriting the experiment's provenance. `source-archive.json` records the relationship.

The four prepared conditional CP pilots were held before launch because three selected cases have these parity contradictions. No solver calls were made by that batch.
