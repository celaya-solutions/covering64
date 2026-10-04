```
Document:    Exact LP Diagnostic for the Fourteen-Cut Pilot Best
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      589c0db8f0829017c400dc4b5537d8e7634a5346ae03d6fa055492436710cd1b
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Exact LP screen of the new ten-hole multicut best

The new ten-hole state from the fourteen-cut pilot passes every stored cut,
but its full ordinary-completion LP is infeasible. An exact signed-row
certificate proves this for its fixed heavy tuple within the regular family.
No CP solve ran.

## Model and bounded solve

`run.py` binds the completed pilot audit and frozen best witness, then copies
the earlier audited 697-row model while adjusting only finite row bounds for
the changed fixed-heavy incidence. The existing independent oracle freshly
reconstructs all 697 rows, 1,200 ordinary columns, original lexicographic IDs,
28 fixed heavy blocks, and the complete 276-heavy symbolic basis. All six hub
graphs remain represented. The source model, builder, oracle, LP helper and
separate replay checker are hash-bound in `manifest.json`.

The GLOP 9.15.6755 pass used one worker, seed 2026104, a ten-second feasibility
budget and at most ten seconds for elastic extraction. Feasibility returned
INFEASIBLE in 0.173858 seconds; the elastic phase returned OPTIMAL in 0.204019
seconds. Total solver time was 0.377876 seconds. The numerical elastic objective
is 16.68585525272344. Numerical statuses alone are not the accepted result.

## Exact certificate and replay

`dual.json` contains integer signed row weights with denominator 1000 and binds
the model, heavy tuple and manifest. The exact contradiction gap is
8269/500 = 16.538. The frozen separate checker replays these weights against
the independently reconstructed symbolic rows, including the fixed-heavy
bound shifts and the ordinary `[0,1]` box maximum. Six damaged certificate
variants are rejected. See `dual-audit.json`.

This exact gap is a certified lower bound on the relevant contradiction, not
an independently certified optimal elastic objective. The new numerical
elastic objective is worse than the previous ten-hole cut-pilot seed's
12.64569999478813, despite passing all fourteen stored cuts. No new reusable
cut was derived here, and no search or CP optimization follows from this
receipt.

## Artifacts and scope

`seed.txt` is the audited near-cover input, not a full covering witness.
`manifest.json`, `lp-result.json`, `dual.json` and `dual-audit.json` are compact
tracked receipts. The full protobuf model, numerical dual and source snapshot
remain in ignored `experiments/scratch/multicut-best-lp-v1.0.0/`.

The conclusion applies only to this fixed-heavy regular degree-20
four-sevenfold family. It neither excludes an entire first-link representative
nor supplies an unrestricted C(16,5,3) bound. The launcher refuses existing
outputs. The narrow Ruff check passed; global checks and Git integration are
owned by the coordinating agent.
