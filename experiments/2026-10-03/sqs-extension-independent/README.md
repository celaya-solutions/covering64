```text
Document:    Independent SQS Extension Construction and Model Gate
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      8f45a18d43e8279a61e00f55a9ef1b9fb8f0faa2082a4becadf7e2e6785417f2
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Result

The frozen two-seed SQS extension model passed the independent gate. This audit
ran no solver. It verifies an exact-64 feasibility encoding within a specified
1,744-block pool; it does not establish completeness for unrestricted
C(16,5,3), feasibility of this model, or any global lower bound.

# Independent reconstruction

`check.py` does not import the primary construction code or model builder. It
reconstructs the affine quadruples by completing each triple: XOR its three
zero-based point labels to obtain the fourth label. It constructs the traded
seed from the transversals of the four pairs (1,5), (2,6), (3,7), (4,8), replacing
the eight affine transversals with the other eight. Direct triple counts prove
that the two trade sides have the same triple multiset.

Both reconstructed seeds contain 140 distinct quadruples and cover every one
of the 560 triples exactly once. Independent binary elimination gives incidence
ranks 11 and 12, which proves that the two seeds are not point-relabelings of
one another. Both the package verifier and standalone covering checker pass
the reconstructed seeds at k=4.

The audit scans all 4,368 five-blocks in lexicographic order and includes a block
exactly when one of its four-subsets belongs to a seed. This differs from the
primary generator, which extends each quadruple by each available point. The
individual pools each have 1,680 blocks; their union has 1,744. The union's triple
support histogram is 336 triples with 30 candidates, 192 with 32, and 32 with 38.
Every saved local ID, global lexicographic ID, block, triple and support list
matches this reconstruction.

A separately constructed 140-block extension cover passes both k=5 covering
verifiers and belongs to the audited union. This is a positive test of the pool
and verifiers, not a 64-block candidate.

# Complete model check

The protobuf contains exactly 1,744 Boolean variables and 561 rows: exact
cardinality 64 followed by all 560 triple coverage rows. The audit checks every
variable name/domain and every row's variable indices, unit coefficients and
bounds. It requires the top-level fields to be only `variables` and `constraints`.
Thus no objective, hint, enforcement literal, fixed block, symmetry rule, degree
restriction, or one-extension-per-quadruple restriction is hidden in this model.

Ten damaged seed controls, seven damaged pool controls, and twelve damaged
model controls are rejected. Checked source, snapshot, seed, pool, construction
audit, manifest and model hashes remain unchanged across the audit.

# Evidence

- `check.py`: reproducible independent construction and full protobuf checker.
- `gate.json`: pass receipt, all source/input hashes, controls, direct counts,
  and both covering-verifier reports.
- `affine-independent.txt`, `traded-independent.txt`, `extension-positive.txt`:
  independently reconstructed positive controls.
- `manifest.json`: hashes of this compact audit.

Frozen model SHA256:
`d0a70c16b53c2399ed10eae2deb77b3c817e352a4fc950d7584291b3c249703f`.

Frozen pool SHA256:
`b1e0e13ac3787643b25e920d2ce8f83d7119dedcb3c78daaf8316e04510c68c6`.

Recheck without solving:

```sh
uv run python experiments/2026-10-03/sqs-extension-independent/check.py
```
