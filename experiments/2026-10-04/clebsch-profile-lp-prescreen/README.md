```text
Document:    Clebsch Recipe Fractional Feasibility Prescreen
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      926f4b6e23e0ffba8dd77d191ebedcbb2f1cc0cf5cc2a15c4a95f95d14f37b6d
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Fractional screen of all sixteen recipe representatives

The sole run tested all sixteen saved regular-tournament Clebsch profile
representatives: seeds 0, 1, 9, 40, 19, 8, 4, 18, 16, 12, 3, 10, 11, 26, 60,
and 25. These are representatives of the previously checked recipe, not a
complete reduction of C(16,5,3).

For each profile, all 4,368 lexicographic five-block variables are continuous
in [0,1]. Each of the 560 triples has its exact demand, either one or two.
Each triple has 78 candidate carriers. Summing the rows gives ten times the
variable sum equal to 640, hence a variable sum of 64. The point and pair
incidence totals also follow from these triple rows and the profile counts.
The source and seed list were reviewed independently before root launched.

All sixteen GLOP calls returned OPTIMAL for the zero objective, with 560
fractional columns each. None supplied an integer cover. Across all saved
vectors the largest triple-row residual was 1.96698213272839e-12, there was no
bound violation, and the variable sums ranged from 63.999999999998266 to
64.00000000000107. These are numerical fractional solutions, not exact rational
certificates and not verified 64-block witnesses. No profile was excluded.

The five-second per-call limit allowed at most eighty scheduled solver
seconds; the whole process had a separate 100-second watchdog. Actual total
solver time was 17.8898922924418 seconds and wrapper time was 18.46554608293809.
All calls completed with exit zero and no watchdog, retry, or continuation.
The source, versions, input hashes, full vectors and result remain saved here.
No integer solver was called. Existing seed-zero integer timeouts and the
fifteen still-untested integer representatives remain distinct from this screen.
