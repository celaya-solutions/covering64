```
Document:    Saved Registry-Eligible Matching Template Seeds
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      165e3954fe87331f9343aa81db8c00b506e516a97bf076f33c0dd0848283fdb0
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

Two saved matching-template native seeds remain open in the current first-link
registry under their intended matching graph 5:

| Seed | Holes | Soft score | Pair-target L1 | Four matching link classes |
| --- | ---: | ---: | ---: | --- |
| Native soft raw best | 17 | 116 | 16 | 057, 064, 043, 013 |
| Native soft score best | 19 | 106 | 6 | 057, 064, 043, 069 |

Their source files are respectively `matching-raw-best.txt` and
`matching-score-best.txt` in `experiments/2026-10-03/four-seven-template-native-soft`.
The later lookahead `matching-seed.txt` is byte-identical to the 17-hole raw
best. The older native 21-hole best is now registry-excluded in graph 5 because
one of its links is matching-029.

The frozen score source independently confirms that graph 5 assigns pair
counts seven to (4,8) and (12,16), and five to all other hub pairs. The target
vector is (7,5,5,5,5,7) in lexicographic hub-pair order. These partial states do
not already satisfy the target equalities: their actual hub-pair counts are
(6,4,5,5,5,7) for the raw best and (6,5,5,5,5,7) for the score best. Registry
eligibility alone establishes neither LP nor integer completion feasibility.

`check.py` independently reloads the current registry and complete link-orbit
archive, verifies both allowable point transports for each of the four links,
and saves every point map and heavy block. It freshly recounts cardinality,
point degrees, missing triples and pair deviations and runs both cover
verifiers on all three historical seeds. `audit.json` binds exact seed,
classifier, scoring-source and registry hashes. No LP or integer solve ran.

The 17-hole state is the lowest-hole matching native template seed located in
the recorded pilot summaries. The 19-hole state is a separate lower-soft-score
alternative; its heavy tuple differs in the fourth anchor link. Neither should
be confused with the forbidden three-hole/core states or the cycle seeds.
