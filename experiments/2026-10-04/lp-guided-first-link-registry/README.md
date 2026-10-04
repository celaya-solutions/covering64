```
Document:    First-Link Registry Audit of Two LP-Guided Heavy Tuples
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      f9f7c8555529fc0a8113d293dc6d59c4673470cba8c66a32d6d71e6a325f83b9
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

The 109 checked exclusions classify seven-block heavy links under a specified
hub graph. They do not classify 20-block point links. This audit reuses the
frozen complete classifier, verifies its full 29,970-link tables and prior
independent archive hashes, and transports each of four anchor links under
all six possible hub graphs. Both allowable graph transports agree in every
case. All 48 point maps, representative edge sets and certificate-source
references are saved in the two `first-link-screen.json` files.

The best broad-LP tuple, with elastic objective 5.575882992498541, has no
registry-open hub graph. The alternate nearest-master step 038 tuple, with
broad objective 5.966796868079938, retains only graph 1.

| Graph | Kind | Best tuple: four link classes | Nearest step 038: four link classes |
| --- | --- | --- | --- |
| 0 | matching | 049, 049, 065, 099 | 049, 049, 065, 065 |
| 1 | cycle | 061, 061, 086, **028** | 061, 061, 086, 086 |
| 2 | matching | 126, 126, 049, 018 | 126, 126, 049, 049 |
| 3 | cycle | 086, 086, **103**, **128** | 086, 086, **103**, **103** |
| 4 | cycle | **103**, **103**, 061, **028** | **103**, **103**, 061, 061 |
| 5 | matching | 065, 065, 126, 099 | 065, 065, 126, 126 |

Every displayed matching class is excluded. Bold cycle classes are excluded;
the other displayed cycle classes are registry-open. Link order is anchor
(1,2,3), (5,6,7), (9,10,11), (13,14,15). Graph indices are zero-based in the
lexicographically enumerated six-graph list.

For the surviving graph 1, the pair order is (4,8), (4,12), (4,16), (8,12),
(8,16), (12,16). Its excess vector is (0,1,1,1,1,0), giving exact pair targets
(5,6,6,6,6,5). A registry-open graph is not evidence of an integer completion:
the saved nearest tuple still has its separately checked positive broad-LP
certificate. Graph openness identifies which constraints to retain in a
subsequent nearby-tuple search.

The saved nearest heavy master was checked against a direct reconstruction of
its first 605 rows: one cardinality row, 52 link-incidence rows and 552
nonanchor-heavy triple caps. Its remaining 238 rows are accumulated exact LP
cuts. It has no explicit registry constraints or hub-graph survivorship
filter. Consequently a low elastic score alone can favor a tuple already
excluded by the first-link registry. This audit does not invalidate those
earlier certificates or change the official 109-excluded/149-open registry.

`run.py` reproduces both classifications without optimization. `audit.json`
binds input hashes and the saved master structure. The 28-line `seed.txt`
files contain heavy pins only, not 64-block covering candidates. A separate
independent map and scope replay is being recorded in the sibling
`lp-guided-first-link-registry-independent` folder.
