```
Document:    Registry-Eligible Seeds Among 115 Saved Heavy Tuples
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      3de356567f6394257fcadd308363abbcc1fbd75c4e5051c85d44e62ef62c5b97
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

The saved 95 nearest-master and 20 margin-master tuples were classified under
all six hub graphs without any new LP or integer solve. Exactly 51 distinct
labeled tuples retain at least one graph under the existing first-link
registry; 64 tuples are eliminated under all six graphs. This uses the
existing 109 checked exclusions and does not add any registry entry.

| Surviving graphs, zero-based | Bit mask | Saved tuples |
| --- | --- | ---: |
| none | 0 | 64 |
| 1 | 2 | 37 |
| 1, 3 | 10 | 1 |
| 4 | 16 | 11 |
| 1, 4 | 18 | 2 |

The five lowest existing **broad all-graph elastic scores** among distinct
labeled survivors are:

| Nearest-master step | Broad score | Open graph | Four cycle link classes |
| ---: | ---: | ---: | --- |
| 038 | 5.9667968681 | 1 | 061, 061, 086, 086 |
| 094 | 6.3899822293 | 1 | 061, 061, 086, 061 |
| 061 | 6.5838634254 | 1 | 061, 086, 086, 061 |
| 091 | 6.6003004822 | 1 | 061, 061, 086, 086 |
| 054 | 7.4261383730 | 1 | 061, 061, 061, 061 |

Every row above retains only graph 1, whose physical hub pair targets are
(5,6,6,6,6,5) on (4,8), (4,12), (4,16), (8,12), (8,16), (12,16).
Only step 038 has a fresh fixed-graph score: **8.0242448155**, with a checked
positive exact certificate. The other broad scores are not evaluations under
their surviving graphs. The table ranks possible new descent seeds, not
feasible LP points or covering witnesses.

`screen_saved.py` loads the separate independent classifier once and checks
all graph/anchor maps against the complete archive. `saved-screen.json`
preserves input/result hashes, each tuple's 28 global block IDs, exact class
IDs under every graph, each surviving mask, the complete eligible ranking,
and all explicit point maps for the top five. Full-tuple isomorphism was not
tested: distinct labeled block sets can still be equivalent after relabeling.
The global lower bound and the 109-excluded/149-open registry are unchanged.
