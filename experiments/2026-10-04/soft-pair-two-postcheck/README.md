```
Document:    Soft Pair-Two Independent Runtime Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      fc42bad29d1ace543669b4fd65b54314b5d9a0478224ceb54dc9bd2ed0d62d1f
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent soft pair-two runtime audit

The sole 120-second, four-worker run finished FEASIBLE with one callback and one final vector. Both vectors contain the unchanged H49 hint: 49 holes, D2max=74, D2sum=170, D3=D4=0, minimum pair count five, and core overlaps [0,2,2,4]. The solver objective is 41,563 with bound zero. No actual zero-D2max hint or cover was found, and no improvement was made.

The callback and final vectors each contain all 5,728 values and match exactly. Every variable domain and all 14,405 serialized rows were checked, including the 13,845 active rows. Exact block, pair, triple and hole values were independently reconstructed. All 10,920 actual pair-two deficits were recomputed, and the saved per-pair detail agrees. Auxiliary deficit slack is zero in both vectors. Both verifiers rechecked the one unique 64-block family. Its independent global profile maximum is zero.

The preflight checker rejected eight damaged vectors and accepted a deliberately increased auxiliary deficit as valid slack. This matters because the model permits d_P to exceed its true deficit. The runner correctly saves both the solver vector and canonical actual values, and its callback stopping rule uses the actual qualified score. Every callback and the final vector are retained, including ties. If a future callback has zero actual deficit with solver slack, that callback remains a witness even if the final solver incumbent differs.

The checked full H49 hint was feasible and canonical before the run. A complete feasible hint does not guarantee immediate solver progress. The actual run used 120.003640 solver seconds and 120.005928 elapsed seconds. Raw response status, objective, bound, timing, source/model/parameter/hint hashes, gate binding and callback count all match the producer result.

This audit imports no producer metric or vector-checking helper and calls no optimizer. Root owns the separately checked serialized-model gate and sole launch. Positive holes remain a noncover; the bounded outcome is not an infeasibility proof or a global lower bound.
