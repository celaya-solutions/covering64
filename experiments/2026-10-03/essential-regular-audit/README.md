```
Document:    Independent point-essential model review
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      184442f3918d19f22b641df5f73651304be3cd97df697322b97693088758118a
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent point-essential model review

The replacement lemma is sound as a joint existence reduction with the degree-19 branch. Every point of a cover has degree at least 19. With at most 64 blocks, either some point has degree 19, or there are exactly 64 blocks and every degree is 20. In the latter case, if a selected block B has a point p with no private triple in B, replacing p by any point outside B preserves coverage and lowers its degree to 19. If the replacement is already present, deleting B preserves coverage and leaves p with degree 19. A 63-block result may be padded to 64 using an unused block avoiding p. No chosen incumbent or rotational restriction is used.

The source uses a true equivalence between each private indicator and coverage count equal to one. Each block-point implication is guarded by that block being selected. Fixing the first lexicographic block is safe by relabeling any selected block to 1,2,3,4,5. Pair multiplicity at least five is necessary for a full cover because a block covers only three of the fourteen triples through a pair. For partial covers this pair restriction and essentiality intentionally narrow the heuristic family; the source metadata labels that scope correctly. No source defect was found.

`check.py` independently enumerates all 1,024 block families on the complete v=5,k=3,t=2 universe. Exactly 106 satisfy point-essentiality, and the encoded model has exactly those 106 assignments with every private indicator matching its independent count. This covers selected and unselected blocks and triple counts zero, one and greater than one. Separately, 256 deterministic normalization trials check bijection, distinctness, coverage multiplicities and all incidence predicates. Both the full and five-hole models pass OR-Tools model validation.

The evidence applies to the source hash in `result.json`; the exact reviewed source is retained at `experiments/scratch/essential-regular-independent-audit-20261003/audited_source.py`. The small-universe check audits encoding behavior, not the existence or nonexistence of C(16,5,3) covers. No unrestricted proof certificate is produced by this audit.

Run from the worktree root:

```sh
uv run python experiments/2026-10-03/essential-regular-audit/check.py
```
