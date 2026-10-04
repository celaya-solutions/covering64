```text
Document:    H11 Union Recombination Counting Certificate
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      0fca75499a6220d6bcf70fd05db0bf4d99f38098d924f6367937c6fa028d67fd
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# The two-family union cannot contain a 64-block cover

The 128-block union of the saved f621 H11/D25 family and the historical 439d H11/D27 family needs at least 73 blocks to cover all triples. This is an elementary, independently replayed restriction on this exact pool. It is not a global lower bound for C(16,5,3), and it does not rule out families using blocks outside this union.

The two 64-block sources share no blocks, and each covers all 11 missing triples of the other. Their union covers all 560 triples. The support sizes are: 20 triples with one carrier, 378 with two, 144 with three, and 18 with four. The 20 singleton triples force 19 different blocks.

After those 19 blocks are selected, 387 triples remain uncovered. Of those, 291 triples have two union carriers, representing 244 distinct pairs of block IDs. A deterministic greedy matching found 54 pairs with no block shared between pairs and no block among the 19 forced blocks. Each selected pair is certified by a triple whose complete carrier set within the union is exactly that pair.

A cover must include all 19 forced blocks and at least one block from every one of those 54 disjoint pairs. Summing these requirements gives 19 + 54 = 73 selected blocks. The supports involve 127 distinct block variables. No solver status, symmetry assumption, pair-floor rule, incumbent-core cap, or unverified pruning claim is needed. The exact minimum within this pool was not investigated.

`certificate.json` preserves both source paths and hashes, full lexicographic block IDs, the 19 singleton certificates, all 54 pair certificates, and the complete incidence binding. Its SHA256 is `f00d4c00966c86c9a474bb2fe8a1641fbdd5ad62a8ecb5e842f08a78e5eaa2fc`. `incidence.json` preserves all 560 support rows, and `union-128.txt` preserves the candidate pool with 1-based labels.

The separate checker recomputes all supports directly from the pinned input families and does not import the producer or replay its matching algorithm. It checks the summation certificate, disjointness, singleton implications, full incidence table, hashes, and all counts. Seven damaged certificates are rejected: duplicate pair, wrong carrier, removed singleton proof, inflated bound, Boolean carrier, wrong union, and changed source hash. Both original families and the full 128-block union are freshly checked by the package verifier and the standalone verifier; they report 11, 11, and zero holes respectively.

`verification.json` SHA256 is `41c4ff2ff3f40247d5d21e50acaf80e2eb9705dc78ec2f283473ca693fc30cf0`. Replay only the finite proof with `uv run python experiments/2026-10-04/h11-union-recombination/check_certificate.py`. The tracked producer preserves the certificate and refuses to overwrite it.

The proposed 120-second CP pilot was canceled before any covering model was prepared or any solver launched. Its unfinished draft runner is retained only in the ignored archive `experiments/scratch/h11-union-recombination-unlaunched-draft-20261004/run.py`; it was never prepared or executed. The counting certificate made that bounded optimizer run unnecessary.
