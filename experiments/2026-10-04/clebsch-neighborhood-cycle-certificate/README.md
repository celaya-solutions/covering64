```text
Document:    Finite Exclusion of the Full Clebsch Neighborhood Recipe
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      a941f4d8fc3d1f26ddae7941e7ea4d568099b8504624f8663a39b22161f672b0
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# A finite conditional exclusion

The certificate rules out exact64 covers having both the Clebsch pair profile
and all sixteen neighbor pentads. It makes no unrestricted nonexistence claim.
The independently checked reduction leaves 192 cycle variables, 240 exact-one
single-edge rows, 160 path rows with bounds one and two, and a sum of 48.

The certificate supplies 192 explicit graph automorphisms taking cycle zero
to every cycle. They preserve the fixed neighbor family and every constraint.
Every proposed solution contains a cycle, so one may map that cycle to zero.
Starting with cycle zero selected, the certificate uses only elementary row
bounds. A saturated upper bound forces the unknown variables to zero; a
saturated lower bound forces them to one. Nine positive trial literals lead
to row contradictions, so their negations are forced in the parent state.
The saved traces end with both cycles (2,6,9,11,16) and (5,8,9,11,16) selected.
They cover the exact-once triple (9,11,16) twice.

The independent checker rebuilt all rows from a different graph presentation,
replayed all 431 force steps and nine failed literals, and checked all 192 maps.
It rejected 27 damaged certificates without importing CP-SAT or the producer's
propagator. Certificate SHA256:
`6802e49098940c70253dbf17e0a44bc05acb800185d85356dc5031faa6c545fc`.
Independent audit SHA256:
`de03e575af4237a99f5ad10083ac7f0651021c8349d3250162cef2972f752e84`.
The neighboring fifteen-neighborhood forcing certificate separately extends
this conclusion to an upper bound of fourteen selected neighbor pentads,
only within the Clebsch pair-profile construction.
