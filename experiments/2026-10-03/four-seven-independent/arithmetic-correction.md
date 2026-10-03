```
Document:    Correction to Four-Sevenfold Double Triple Counts
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      4155e35884ab6e872a3ee97335ce583ee701e1b73ffc34a4d3bbe2b481aec296
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Correction to the triangle-class arithmetic

The frozen `README.md`, in its paragraph beginning “Its anchor degrees are seven”,
states the three-anchor triangle count as `14-2z`. The correct count is `14-z`.
The complete identity is

`(N0,N1,N2,N3) = (z, 18-3z, 12+3z, 14-z)`.

Here `Nr` counts the 44 remaining double triples with exactly `r` anchors, and
`z=N0`. Their hub-hub pair incidences total 18, so `3z+N1=18`. Their anchor-hub
pair incidences total 60, so `2N1+2N2=60`. Their total cardinality is 44, giving
`N3=44-z-N1-N2=14-z`. The earlier expression would sum to `44-z` instead of 44.
The existing range `z in {0,1,2}` is unchanged.

This correction affects only the explanatory arithmetic sentence and the first
version of the standalone integer-pattern checker's bookkeeping assertion. No
covering model, pair-demand model, LP witness, or row audit used the wrong formula.
The frozen README is retained unchanged for provenance. Corrected pattern checks,
unchanged integer witnesses, and saved solver-status evidence are in
`../four-seven-double-patterns/`.

The header hash is over this body, including its initial blank line.
