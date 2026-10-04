```text
Document:    Independent Combined Template and Hub Exclusion
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      748b6de38b95500224094ebaa2c0ee28716f432cc99fa3b170276794906156e4
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independently checked result

Matching-032 is excluded in all six necessary hub-count cases. Five cases
already had exact independently replayed certificates from the hub campaign.
The remaining case, `(m4,z)=(0,1)`, now has an independently replayed positive
gap of `7651/1000000` using the complete template hull and its two hub-count
equalities. All six case proofs are linked in `matching-032-audit.json`.

The new raw matrix has 61,576 variables in [0,1] and 4,559 rows including its
seven fixed-link equalities. The checker verifies byte hashes, preserves all
4,550 original independently audited template-hull rows exactly, and separately
reconstructs precisely two new hub equations from all 4,368 global blocks:
no four-hub blocks, and exactly five all-hub-triple incidences. It independently
reconstructs the seven selected block IDs and recomputes the certificate's
integer weighted bound and box maximum. Eight damaged proof controls fail.

This adds one ID to the previous checked union of 105. The total is now 106
excluded first-link representatives and 152 open: 102 cycle and 50 matching.
`combined-first-link-exclusions.json` preserves every proof source and the
complete surviving ID list. Different necessary LP relaxations may be used
for different hub cases; each exact contradiction excludes the same stated
integer subcase. All six must be excluded before counting the first-link ID.

# Scope and preservation

This excludes only the stated fixed-first-link integer regular four-sevenfold
branch. It does not exclude the whole regular branch or prove an unrestricted
lower bound for C(16,5,3).

The new proof's raw files are in
`../../scratch/four-seven-template-hub-priority-20261003/matching-m4-0-z-1`.
The original hull input and its independent matrix audit are unchanged.
`evidence.json.gz` stores the complete sparse integer certificate, seven fixed
rows, two hub rows and the six-case audit. Its SHA256 is
`1dfb1b8bc23d5da800bd05036eeda7e139b35affafdf9aebfc2cb721316c1de2`.

Replay without calling a solver:

```sh
uv run python experiments/2026-10-03/four-seven-template-hub-independent/check.py
```
