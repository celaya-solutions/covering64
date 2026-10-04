```text
Document:    Soft Pair H12 Completed Outcome
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      23e2ad54d7e1c55cbef8769c43308e3f1c5d2f012f1880d9aa864a3493aea4c4
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Completed outcome

The sole declared 300-second, four-worker run (seed 2026104901) returned FEASIBLE after 300.012574 solver seconds. Three callbacks and one final vector contain two distinct families. Independent recounts, every domain/row check, and both covering verifiers passed the expected partial-family checks; no covering witness was found.

Actual maximum-per-pair and full-row deficits fell from 34 to 32. All 12 missing triples remained unchanged. The single block replacement removes {4,5,7,10,15} and adds {5,7,10,12,15}. Callback2 contains one valid unit of solver auxiliary slack; callback3 and final have canonical objective 17,964. The bound stays zero and actual D2 never reaches zero.

The independent runtime receipt is `../soft-pair-h12-postcheck/postcheck.json`, SHA256 `a27cd62205199d45621417e45f1320fbe6dbea077b00149ef0b5017b7231b16a`. The durable best-family copy is `../soft-pair-h12-relabel-novelty/final-family.txt`, SHA256 `cadb86e4f2243eada269dc314bca0bc5c238f5b0ca2bd9525dd0b67aad24c970`. That independent novelty receipt also certifies overlap at most 55 with every relabeling of the old core. This is a verified noncover and a better soft-model hint, not a solution or lower-bound proof.
