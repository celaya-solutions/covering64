```
Document:    First Family Encoding and Orbit Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      c5b2410f5fda05f2716d43f8f654be14c9c8303d498ecd61102f8050eaec45f8
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

This audit checks the 13 first-family cases and their exact CP-SAT encoding. It does not prove that any case is impossible.

## Scope and completeness

The claim is conditional on a point-essential, regular degree-20 cover in the normalized sevenfold-triple branch. The heavy triple is 123. Its seven blocks use the outside edges 45, 46, 78, 9-10, 11-12, 13-14, and 15-16.

The independently checked local classification gives exactly the PG, r4, and r6 local family types. Essentiality of point 4 in the two spoke blocks requires some local family to omit 45 and some local family to omit 46. Permuting the three anchors and, when needed, exchanging the spoke leaves lets the first local family omit 45. It cannot be PG. The first family therefore comes from the r4 or r6 pools used here.

The audit independently enumerates every source-point map whose missing matching includes 45 and lies in the seven-edge graph. It checks 460,800 r4 maps and 46,080 r6 maps, yielding 28,800 and 15,360 distinct first families. An independently constructed group of 3,840 outside permutations fixes the omitted spoke and preserves the graph. Its disjoint orbits reproduce exactly the nine r4 and four r6 representatives. Every one of the 44,160 archived source-to-family and family-to-representative maps is checked on all 13 quadruples.

## Encoding check

All 13 saved full-cover models match independently reconstructed rows: 4,944 variables and 3,086 constraints each. The block variables follow all 4,368 lexicographically ordered five-subsets on labels 1 through 16. The first 20 blocks are fixed; the remaining permissible blocks are unrestricted within this branch.

The rows enforce 64 blocks, regular degree 20, anchor-pair degrees 7, anchor-to-hub degrees 6, other anchor-to-outside degrees 5, and outside pair degrees at least 5. Each of the other two local families covers all pairs outside the seven-edge graph, has deficit 0, 4, or 6, and omits at most one spoke. At least one of those families omits the opposite spoke, 46.

All triples have exact uncovered indicators. Full-cover mode allows zero uncovered triples. Other private-point constraints are omitted, so the model contains a superset of the intended point-essential branch. This omission cannot remove a completion from that branch.

## Positive and damaged controls

The saved `positive-partial.txt` is the verified 27-hole construction relabeled into representative `r6-000`. It has 64 distinct blocks and remains an incomplete cover. Its full assignment satisfies all 3,086 rows when the hole budget is 27. The exact point map, both cover-checker reports, and hashes are saved in `positive-partial.json`.

Twelve controls reject damaged rows, domains, ordering, allowed deficits, family maps, input quadruples, or the positive assignment. No solver result is used to establish these audit checks.

Run the complete audit from the repository root:

```sh
uv run python experiments/2026-10-03/first-family-independent/check.py
```

`result.json` records the exact source, input, map archive, generated model, and saved model hashes. Large generated model files remain in ignored scratch storage.

## Hinted and relaxed partial models

`check_hint.py` independently recounts all 4,944 values in the actual saved 27-hole hint, verifies its objective and every row, and rejects six damaged hints. This check invokes no solver.

The later explicit relaxed mode removes exactly 79 rows: 78 outside-pair lower bounds and one opposite-spoke requirement. `check_relaxed_hint.py` verifies all 3,007 remaining rows and the complete 14-hole hint, with three damaged controls. The new builder's 13 default models remain byte-identical to the original saved full-cover models; `default-equivalence.json` records that comparison.

`normalized-h14.txt` is a relabeled native-search partial candidate in first-family case `r4-000`. Both cover checkers agree on its 14 holes. It has pair deficit 7, no opposite-spoke omission, and one unsupported block-point occurrence. Those properties are recorded in `normalized-h14.json`; it is not a positive control for the strict model.

The later structured five-hole candidate is normalized to `r4-005` in `normalized-h5.txt`. It has pair deficit one, no opposite-spoke omission, and five unsupported block-point occurrences. The same exact point map is applied to the eligible six-hole escape in `normalized-escape-h6.txt`. Both maps are independently checked on all 696 point, pair, and triple incidences; all 3,007 relaxed rows and all 4,944 complete hint values are checked without a solver. Damaged map and hint controls are rejected. The escape has only four multiplicity-at-least-six triples, all with multiplicity seven, so it avoids the tested forbidden five-triple profile. These files remain partial candidates.
