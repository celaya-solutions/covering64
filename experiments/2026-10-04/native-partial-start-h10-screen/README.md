```
Document:    Native Partial-Start H10 Relabel and Profile
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      735018e961985b400a6feecf57bd301eb688e8e3dfbf0c82fb30375530deabe2
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Native partial-start H10 screen and profile

The H12-started native run improved its saved admissible 64-block family from 12 holes to 10 holes. The H9-started run retained its existing nine-hole family. This check selected the genuinely improved H10 final family and confirmed that its raw/admissible final ties are the same bytes. It remains a noncover.

Both the package verifier and separate standalone verifier confirm 64 distinct blocks and the exact ten uncovered triples. The final profile is:

| Measure | H10 |
|---|---:|
| Point multiplicity histogram | 19:3, 20:10, 21:3 |
| Pair multiplicity histogram | 4:2, 5:79, 6:36, 7:3 |
| Minimum pair count | 4 |
| Single-triple deficit: sum of pair maxima / full row sum | 7 / 54 |
| Quadruple deficit: sum of pair maxima / full row sum | 4 / 48 |
| Two-triple deficit: sum of pair maxima / full row sum | 23 / 359 |
| Two-triple violated rows / pairs | 225 / 20 |
| Four named core overlaps | 1, 0, 1, 0 |

Histogram entries mean `multiplicity:number of points or pairs`. Full row sums use all 1,680 single-triple rows and each set of 10,920 quadruple and two-triple rows. Counts were checked by direct set containment and subset enumeration, preserving the original point labels and lexicographic block order.

The frozen relabel helper found zero necessary partitions, certifying overlap at most 55 with every point relabeling of the original 60-block core. Its arithmetic controls passed. The maximum across the 242 explicitly checked images is 4; that finite-image maximum is not a global maximum. The all-relabel conclusion uses the empty necessary-partition set.

H10 fails the current soft model's pair floor and single-triple rows. Its lower hole count does not make it a feasible replacement for the legal H12/D2=32 complete hint. This report does not qualify it as a zero-deficit hint or a cover.

`h10-family.txt` is a durable exact-byte copy of the selected final family, SHA256 `a8f2258c5a194307954bcaf11b6dfd186753841ba26ec5d1a52f9aa6852a6f07`. The original producer files remain unchanged. `diagnostic.json` binds the terminal campaign, prior independent runtime audit, start, selected family, both verifier receipts, relabel result, full profiles, and block/hole differences. No optimizer was called, and this result makes no global lower-bound claim.
