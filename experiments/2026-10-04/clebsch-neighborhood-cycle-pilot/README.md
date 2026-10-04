```text
Document:    Clebsch Neighborhood and Cycle Pilot
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      3ce9f4d181ce06b91c16a71f35246f2d7bd165954323d0ddab0a695fe17fdf8f
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Result and conditional construction

The sole 30-second-budget, one-worker CP-SAT call returned INFEASIBLE during
presolve in 0.015652 native seconds. The saved wrapper took 0.759248375 seconds,
exited normally and did not trigger its 35-second watchdog. No vector or
witness exists. The solver result alone is not an independently checked proof.
The subsequent finite certificate is a separate artifact, independently replayed.

This model assumes the Clebsch pair profile: multiplicity six on graph edges
and five on nonedges. It additionally fixes all sixteen neighbor pentads.
The previously proved triangle-free pair-profile consequence requires every
non-path triple exactly once and every two-edge path once or twice. The fixed
pentads cover all 160 independent triples exactly once. Any further pentad
can therefore have no independent triple, which on five triangle-free vertices
forces an induced five-cycle. There are 192 such cycles. The model retains
all 4,368 global lexicographic variables: sixteen fixed one, 192 free binary,
and 4,160 fixed zero. It has exact64 and all 560 triple rows, with no hint or
objective. Each of 240 single-edge triples has four cycle carriers; each of
160 path triples has six. The exact single-edge rows imply the intended
pair counts within this cycle domain.

Independent review rebuilt the graph by a four-cube plus antipodal edges,
checked every variable and row, and rejected twenty damaged models. Runtime
audit checked all saved bindings and absence of vectors. See the adjacent
independent and runtime-independent folders. The separately checked exclusion
certificate is in `../clebsch-neighborhood-cycle-certificate/`. Neither this
model nor that certificate rules out general Clebsch-profile covers or an
unrestricted 64-block cover.
