```
Document:    D28 Two-Swap Tie Relabel and Novelty Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      be39b762ee716d66c70ce11da4c627404518ee72f03831e6e743b6a74bf02d4f
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Six checked D28 ties

All six saved best ties from the two-swap v2 scan have 64 distinct blocks, 12 uncovered triples, D2max=D2sum=28, D3=D4=0, and minimum pair count five. Fresh package and standalone verifier runs confirm each noncover and its exact hole list. The same recount and dual-verifier checks were repeated for the prior D29, D31, and D32 families. This audit makes no solver or neighborhood-enumeration calls.

Every new family has zero necessary partitions in the frozen old-core relabel screen. Its arithmetic controls passed. Therefore every relabeling of the original 60-block core overlaps each exact family in at most 55 blocks. The maximum across 242 explicit images is four for every tie; only the empty necessary-partition set establishes the all-relabel bound.

The representative is `representative.txt`, copied byte-for-byte from the producer, SHA256 `c6d132069270ead505488fa863a12a0f16a82e289c989a1c4d5961b13826e06f`. The six `tie-*.txt` witnesses were reconstructed from the pinned D29 family and each recorded outgoing/incoming pair. Every canonical byte hash matches the producer's corresponding saved tie hash. No lost historical witness is inferred.

The representative removes `{1,6,11,14,15}` and `{2,5,6,7,8}`, then adds `{1,6,14,15,16}` and `{5,6,7,8,11}`. Compared with D29, it fills `{1,15,16}` and `{5,8,11}` but creates `{1,6,11}` and `{2,6,8}`. Six unit pair deficits disappear and five appear. Its point and pair histograms stay unchanged, while its total deficit falls by one.

| Tie | Distance from D29 | From D31 | From D32 | Pair histogram (count: number of pairs) | Named core overlaps |
| --- | ---: | ---: | ---: | --- | --- |
| 1, representative | 2 | 4 | 2 | 5:84, 6:32, 7:4 | 1,1,1,2 |
| 2 | 2 | 4 | 2 | 5:84, 6:32, 7:4 | 1,1,1,2 |
| 3 | 2 | 5 | 3 | 5:85, 6:30, 7:5 | 1,0,1,3 |
| 4 | 2 | 5 | 3 | 5:83, 6:34, 7:3 | 1,1,1,1 |
| 5 | 2 | 5 | 3 | 5:84, 6:32, 7:4 | 1,0,1,1 |
| 6 | 2 | 1 | 3 | 5:81, 6:38, 7:1 | 1,1,1,2 |

The four distinct pair histograms certify at least four classes that cannot be related by point relabeling. No full isomorphism classification is claimed within equal-histogram groups. D2 is also invariant under point relabeling, so none of these D28 families is merely a relabeling of the D29, D31, or D32 comparison families.

Tie 6 has the same uncovered triples as D29 and is only one replacement from D31. The other five ties move the hole set without reducing its size. The six new ties have pairwise replacement distances from one to four. Ties 1 and 2 are one replacement from saved alternate D29 ties; the complete distance tables, block changes, hole changes, pair-deficit changes, and profiles are in `audit.json`.

The producer reports a completed exact-distance-two shell: 18,668,272,896 possible unordered neighbors accounted for, 1,109,680 pair-floor-eligible completions evaluated, 413,275 satisfying the scan's full named weak rules, and six best ties at H12/D28. This audit binds that terminal result and preserves its selected families; it does not independently repeat the enumeration. Runtime accounting is checked separately.

The frozen radius-four preparation retains its original D29 representative as center. All six D28 families are at distance two from that center, but each violates its at-most-11-hole row. They are partial progress, not covers or zero-deficit hints. No search-center change, global lower bound, or claim about unrestricted existence follows from these diagnostics.
