```text
Document:    Independent Strong Core Release Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      58b4dd2b58dd2d7b0430b04f04985582dbeed9b0e75d0f1ba278ce6c4dfa073d
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent strong-core release audit

The independent preparation gate and result audit passed. The auditor made no
optimizer calls. Both declared producer calls used 120 seconds, four workers,
and seed 2026104102. They used the unchanged 952-block adaptive pool and the full
4,368-block universe, with all 64 slots released.

The entire model and hint were reconstructed independently. Replacing the two
new core upper bounds of 55 by 59 and restoring the previous hint recovers the
previous frozen model bytes exactly. Thus no other constraint or objective was
added. The two existing profile cuts and objective `65 * holes + core_overlap`
are unchanged. The exact proof audit in `core-cap-independent` supplies the
55-block cap for both named core images.

All 36 checked candidate paths were recounted. Ten pass both core and profile
restrictions. Sorting by holes, original-core overlap, and path selects the
14-hole hint with core overlaps 1 and 7 and objective 911. The hint passed both
covering verifiers as a well-formed noncover. Six damaged model controls were
rejected before the producer was given GO.

## Checked results

| Pool | Status | Holes | Original-core overlap | Objective | Numerical bound |
| --- | --- | ---: | ---: | ---: | ---: |
| Adaptive 952 | FEASIBLE | 13 | 1 | 846 | 0 |
| Full 4,368 | FEASIBLE | 3 | 1 | 196 | 0 |

The adaptive and full calls used 120.008262750 and 120.008840000 wall seconds.
There are two saved adaptive improvements and eleven saved full improvements.
Both native final responses differ from their last callback family, with 59 and
60 common blocks respectively. All 15 saved/final records were independently
recounted, checked against every active model row, and checked by both covering
verifiers. Seven damaged responses and three malformed witness controls were
rejected.

Eight full-pool records contain the newly observed forbidden five-heavy
partition, including both three-hole callback states and the native final:

```text
(1,2,3), (5,6,7), (8,12,16), (9,10,11), (13,14,15)
```

The native final multiplicities in that order are 7, 7, 7, 7, 6. The five triples
are disjoint, so the previously checked five-heavy theorem applies directly.
The adaptive records contain no five-heavy obstruction. These statements come
from enumerating every five-tuple of triples with multiplicity at least six;
the scan is not limited to the two modeled partitions.

## Broader relabeled-core screen

The canonical 60-block core has five disjoint triples, each of multiplicity six.
If a candidate family shares at least 56 blocks with any relabeling of that core,
at most four core blocks are absent. Each block can contain at most one of those
five triples. Therefore their total deficit below multiplicity six in the
candidate is at most four. Additional candidate blocks cannot increase that
deficit.

`relabels.py` enumerates every disjoint five-triple set whose total deficit is
at most four. It keeps all triples of count at least two, orders them by deficit,
and visits every disjoint choice within the budget. Its only cost pruning uses
the fact that every later deficit is at least the current one. It was compared
with unpruned enumeration on arithmetic controls, and checks the core's positive
control and a zero-count negative control. If no qualifying partition exists,
the test rules out overlap above 55 for every point relabeling. A qualifying
partition alone is inconclusive.

Every one of these 15 records has exactly one qualifying partition, so that
necessary-condition test alone does not settle their core overlap under all
relabelings. A separate declared screen checks both named core images composed
with every single point transposition, giving 242 distinct explicit images.
It finds no cap violation; maximum checked overlaps are 11 or 12. This explicit
screen is limited to those images. The sibling audit
`relabeled-core-filter-proof/audit.json` independently checks the necessary
condition and recursive enumeration, including positive and threshold controls.

The later sibling transport search found a complete old-core image in the full
three-hole final. `third-core-independent/audit.json` verifies its explicit
point map directly and checks all 60 core blocks, the entire block/triple
bijection, and the transported cap of 55. All three-hole records have overlap
60 with this third core. Along the full-pool trajectory, the 10-hole and 8-hole
records have overlap 55, the 7-hole record 57, the 6-hole record 58, and both
5-hole records 59. The 8-hole state already has the new five-heavy obstruction.
This later positive witness resolves the necessary-condition screen's
inconclusive result for those states without changing any frozen solver model.

No result here is a cover or an unrestricted lower-bound theorem. The full
three-hole result exposes a further proved obstruction that was not yet in
the frozen models. Raw solver files remain in ignored scratch storage and are
bound by the gate and postcheck hashes.
