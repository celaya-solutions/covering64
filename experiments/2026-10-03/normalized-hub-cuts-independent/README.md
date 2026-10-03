```
Document:    Independent Normalized Hub Cut Model Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      28dfbe5345130839b041eb9beab4ba87ffd35a0d189f8409e957c552e81c99e5
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent saved normalized-hub model audit

The saved `first-family-hint-r4-005-hub-lns-20261003` model passes independent
reconstruction of its 325 new hub rows and verification of its complete hint.
It contains 6,428 variables and 7,254 constraints. Every hint value is independently
derived from the h9 candidate and every saved constraint is evaluated without
calling a solver. The prior 6,929 rows match the previously audited combined
model exactly, except row 1,121 increases the global hole allowance from six to
nine. There are no new variables.

The new rows consist of:

- 105 equalities setting the exact-six-or-higher flag to zero for triples through
  normalized hub 4.
- 220 implications, one per triple U contained in {5,...,16}: if μ(U)≥6, at most
  one selected block contains U together with point 4.

The root triple {1,2,3} is sevenfold and has repeated hub 4. In a full regular
cover, that role spends three of hub 4's five pair-excess units. Another heavy
triple cannot contain a root anchor, by heavy-triple disjointness. A disjoint
heavy triple through 4 would require four more units at 4, while another heavy
triple with 4 as a repeated outside point would require three more. Both are
impossible. Thus these rows are safe full-cover consequences within this
normalized regular branch. They intentionally further restrict partial search;
they are not global nonexistence statements.

Six negative controls reject a missing row, a relaxed through-hub bound, a
relaxed reuse bound, wrong implication polarity, a wrong block coefficient,
and the old six-hole hint that repeats hub 4. The new nine-hole hint is byte-for-byte
the separately recounted witness in `regular-heavy-hub-bound`; that audit holds
both cover-check reports and the complete heavy/hub profile.

The checker imports generic row normalization and constraint-evaluation utilities
from the frozen independent `heavy-residual-independent/check.py`. It does not
import the production cut helper. All production snapshots are only hash-checked
as evidence. The result records model, source, checker, and utility hashes.
The larger model remains outside Git in ignored scratch.

Run from the worktree root:

```sh
uv run python experiments/2026-10-03/normalized-hub-cuts-independent/check.py
```

Model SHA256: `dbc6cae2d651f5fbb2f7d03074344147d664c18583c05a9c441cbfc45eb061b1`.
This audit establishes saved assignment feasibility and faithful encoding of
the new rows. It does not establish existence of a complete cover.
