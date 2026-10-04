```
Document:    Soft H12 Final Relabel and Novelty Check
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      36ca48c97322c77e0b8d7d064b5daa0d8828f44461c144b2aea187f44d47b4b1
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Final-family relabel and novelty check

The final soft-pair H12 family remains a noncover with the same 12 uncovered triples as its start. It replaces exactly one block: `{4,5,7,10,15}` becomes `{5,7,10,12,15}`. The other 63 blocks are unchanged. This removes the unit two-triple deficits for pairs `{5,12}` and `{10,12}`, reducing both D2max and D2sum from 34 to 32. No hole was filled or newly created.

Both the package verifier and separate standalone verifier agree on 64 distinct blocks and the exact uncovered-triple list. The final family still has minimum pair count 5, D3 = D4 = 0, and four named core overlaps `[1,1,1,2]`. Its point-count histogram is `{19:6,20:4,21:6}` and its pair-count histogram is `{5:85,6:30,7:5}`. The differing deficit sums are invariant under point relabeling, so this family is not merely a point relabeling of the initial H12 family.

The frozen all-relabel helper found zero necessary partitions. This certifies overlap at most 55 with every point relabeling of the original 60-block core. Its arithmetic controls passed. The maximum over the 242 explicitly checked images was 4; that finite-image maximum is not a global maximum. The all-relabel conclusion comes from exhausting the necessary partition condition.

`final-family.txt` is an exact-byte copy of the producer's raw final witness. Both have SHA256 `cadb86e4f2243eada269dc314bca0bc5c238f5b0ca2bd9525dd0b67aad24c970`. The original raw file is unchanged. `diagnostic.json` binds the producer manifest and terminal result, independent runtime postcheck, prior H12 profile and relabel screen, helper, both verifier receipts, full profiles, and exact block/hole differences. Full CP vectors and model artifacts remain in ignored scratch.

No optimizer was called by this check. Actual D2 remains positive, so no feasible zero-deficit guidance for the hard top-two model is claimed. The small deficit improvement supplies no global covering-number or lower-bound conclusion.
