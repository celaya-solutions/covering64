```text
Document:    Matched Adaptive-Pool and Full-Universe Six-Hole Release Outcome
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      ea3b8971079a4fe6f6bf313b44016a60d12f6104d37b2050a2b67ef23c31aad2
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Outcome

The two authorized cases each ran once. Both returned FEASIBLE with composite
objective 449: six missing triples and 59 blocks from the original 60-block core.
Neither improved the hole count or core-overlap tie score. Both objective lower
bounds were zero, so neither result proves optimality or excludes a cover.

| Case | Available blocks | Wrapper seconds | Callback records | Final result |
| --- | ---: | ---: | ---: | --- |
| Adaptive hole-carrier pool | 952 | 120.02944720897358 | 1 | 6 holes, core overlap 59 |
| Full block universe | 4,368 | 120.02984633401502 | 1 | 6 holes, core overlap 59 |

Each callback recorded the initial hint. Each final native response gave a
different equal-score block set: the adaptive final shares 62 blocks with the
hint, and the full-universe final shares 60. These final ties were saved
separately, giving four records and three distinct block families. All four
records passed both covering verifiers. An exhaustive scan of the heavy triples
found no disjoint-five-heavy obstruction in any saved or final state. Seven
damaged native responses and three malformed witnesses were rejected by the
independent postcheck; each malformed witness was checked by both verifiers.

# Frozen design and evidence

Both cases used the checked elite final six-hole hint, seed 2026104101, four
workers, and a 120-second solver limit. The adaptive pool is the previous
277-block elite pool plus all 720 carriers of the twelve distinct holes in four
checked six-hole states; their union has 952 blocks. The second case releases
all 4,368 blocks. Both release all 64 selected slots.

Each model has 4,948 variables and 1,166 rows. Both retain the two declared
core-at-most-59 rows and two declared five-heavy partition cuts. There is no
additional overlap cap, radius, fixed heavy family, symmetry, or degree
restriction. The objective is 65 times the hole count plus original-core overlap.
Overlap is at most sixty, so one fewer hole always wins. This term only orders
states with equal hole counts. No extra solve or adaptive separation was run.

The independent gate rebuilt both complete models, all hints, the pool and the
shared parameters, and rejected nine damaged model controls. The independent
postcheck extracted both native final assignments, compared saved families,
recounted all profiles and ran both verifiers. Gate and postcheck sources and
receipts are in `../six-hole-pool-release-independent/`.

Key SHA256 values:

- Frozen producer source: `68d5f0ffc21d3f69ed6d99d6004d3b23ec2ef1213b977220173eaaea4d4d0f04`.
- Frozen manifest: `84eac4c5110c0f98c7f8e0b01b3cc29dcc1f51003fdad9aa1b8e502813e2be8c`.
- Gate: `0985c255c2e82ed13d763e2a28e634b412c3f783fa3445667bc0ec9677158cc7`.
- Result: `e884f4d7511aa859cb4024a9541a50fb382607186d4f32c28b756a8eec4a03df`.
- Postcheck: `8e3fa5bcfa334e8ad0de01f7a7dfd914f0150ecdc87f48041dad55ffd7a82fdb`.
- Adaptive final: `609eee3c3354d7b6f5e5886042e7dbe393df874d59634879f6afa3e71a1dbfcf`.
- Full-universe final: `84740692cc03489452bb84d32ab425a8c8cc07644ea959263fbfc857bcd18e02`.

Full native models, parameter protos, responses and solver logs remain in the
ignored `experiments/scratch/six-hole-pool-release-20261004/` folder. The manifest
and result bind their hashes. This bounded comparison found no 64-block cover,
no better partial and no exit from the observed 59-core-block basin. It is not a
global lower bound or a proof against other constructions.
