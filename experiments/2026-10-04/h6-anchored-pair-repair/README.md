```text
Document:    H6 Anchored Pair Repair Profile
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      0eacb5445b03d05beab75b907ccf5ef2af9a7cd5416ee8d2ce1cb62f5142832e
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Fixed source and scope

The source is the saved H6 family with hash
`2d018ffa5e3e424193a4197b23891b52fa59b7ca411d06108e0ab1666bb85855`.
This is a finite carrier/count analysis, not an optimization campaign. It
recounts all 64 one-block deletions after one specified addition and all 2,016
two-block deletion supports after that addition. Exactly three resulting
64-block families are saved and checked by both real covering verifiers.
The source, the intermediate 65-block family, and all three final families
are partial covers. The 65-block family here is not the complete65 baseline.

# Unique simultaneous pair repair

The deficient pairs are {4,6}, {5,6}, and {10,12}, all of multiplicity four.
Their five endpoints force the unique simultaneous repair block
`B* = {4,5,6,10,12}` (global lexicographic ID 3106). It fills three original
holes: {4,5,6}, {4,10,12}, and {5,10,12}. Adding it without removing anything
produces a 65-block H3 partial with pair floor five and D3 = D4 = 0. Its three
remaining holes are {1,7,10}, {4,6,9}, and {5,6,9}.

Every possible one-swap pair-floor repair must add B*, because one added block
must contain all three originally deficient pairs. After adding B*, each of
the 64 original blocks contains at least two pairs whose new multiplicity is
exactly five. Removing any such block makes those pairs deficient again.
The profile saves all 64 rows. Thus no one-swap pair-floor repair exists.

# The complete B*-anchored two-swap check

Keep B* as one of two additions and remove any two original blocks. Of the
2,016 deletion pairs, 733 leave a pair needing two further incidences and
cannot be repaired by a single remaining block. Another 1,280 require more
than five distinct endpoints in the remaining block. The other three each
force exactly five endpoints, hence exactly one possible remaining addition.

All three remove {6,9,12,14,16}. Their other exchanges and final direct counts
are:

| Other removed block | Other added block | Holes | D2max | D2sum | D3 | D4 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 2 10 13 14 16 | 2 6 13 14 16 | 11 | 23 | 48 | 1 | 0 |
| 3 10 11 14 16 | 3 6 11 14 16 | 9 | 21 | 38 | 1 | 0 |
| 8 10 14 15 16 | 6 8 14 15 16 | 11 | 23 | 48 | 1 | 0 |

Each has pair floor five and passes all six named caps, with overlaps
{0,2,2,1,0,0}. Each fails the same remaining single-triple row: pair {6,9} has
count five while triple {6,9,10} has count three, so `13 - 3*5 + 3 = 1`.
Therefore none is weak-qualified. This closes only the B*-anchored two-swap
pair repair. A two-swap repair using different additions, a larger exchange,
or an unrestricted construction remains outside this check.

`profile.json` SHA256 is
`4f7163a2648c9dd72e7e98b0b341bb76108c288e14ff50631ffe3b173e47eeea`.
It includes source/input hashes, all count evidence, the three exact support
completions, and package plus standalone receipts for every saved family.
The checker performs no optimizer or native search calls and refuses to
overwrite a frozen profile.
