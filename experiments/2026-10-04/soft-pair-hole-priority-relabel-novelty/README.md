```
Document:    Hole-Priority Final Relabel and Novelty Check
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      d855f1a8c67031a3d9fc4ddd5c394077a850443e62d19722d2cae57c80fdda16
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Hole-priority final family

The hole-priority run ended with the same 12 uncovered triples as its H12/D2=32 start. Actual D2max and D2sum fell to 31. Both verifiers confirm 64 distinct blocks and the exact uncovered-triple list. D3 and D4 remain zero, the pair minimum remains five, and the four named core overlaps remain `[1,1,1,2]`.

The final family shares 62 blocks with the start. It removes `{5,7,10,12,15}` and `{7,9,12,15,16}`, then adds `{5,7,10,15,16}` and `{7,9,12,14,16}`. Three unit pair deficits disappear and two appear, for a net decrease of one. No uncovered triple is filled or newly created. The changed deficit sum rules out a mere point relabeling of the starting family.

The final point-count histogram is `{19:5,20:6,21:5}`; its pair-count histogram is `{5:82,6:36,7:2}`. The previously proved pair-floor endpoint rule, applied to these freshly recounted counts, gives forced-set sizes `{0:2,3:2,4:6,5:54}` and 8,828 pair-floor-legal single replacements. These new formula counts do not claim a second exhaustive replacement replay. They do not check the other model constraints for those replacements.

The frozen old-core helper found zero necessary partitions, certifying overlap at most 55 with every relabeling of the original 60-block core. Its arithmetic controls passed. The maximum among the 242 explicit images is 4; only the empty necessary-partition set supplies the all-relabel conclusion.

`final-family.txt` preserves the exact producer bytes, SHA256 `a00c567a97a00429063ec599728e8b16fe3ed2c230c9eaffdf99939d7632563c`. The original raw family is unchanged. `diagnostic.json` binds the producer manifest, terminal result, independent runtime audit, prior family, both verifier receipts, full profiles, and precise differences. Models and full solver vectors remain in ignored scratch.

No optimizer was called by this audit. The final family remains a noncover with positive actual pair deficit, so it is not qualified as feasible zero-deficit guidance for the hard top-two model. Neither this result nor the pair-floor characterization makes a global lower-bound claim.
