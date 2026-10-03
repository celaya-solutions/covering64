```
Document:    Selected Heavy Triple Hub Encoding and Pilot
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      371aa5ab00dab5156d5909abbfe836012bf7866cdc837b185ec4c0bab848ff5a
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

This helper tracks repeated outside hubs for the four selected triples 123, 5-11-16, 7-10-13, and 8-9-14. It does not require those triples to remain heavy, and it does not encode every possible heavy triple's hub. Its point-packing rows include all 560 heavy-six flags, so a selected hub cannot also be an anchor of an unselected heavy triple.

## Why the cuts preserve regular full covers

Assume a full 64-block C(16,5,3) cover with degree 20 at every point. Every pair occurs at least five times, leaving exactly five pair-excess units at each point. A triple with multiplicity at least six has all three internal pair multiplicities at least seven. Its two internal pairs therefore spend at least four excess units at each anchor. This also makes heavy triples disjoint.

If an outside point appears in at least two common blocks of a heavy triple, each pair joining it to an anchor has multiplicity at least six. Each anchor has only one excess unit left, so the triple has at most one such outside point. The repeated count is at most three. The hub spends at least three excess units, so it cannot be an anchor of a heavy triple and cannot serve two disjoint heavy triples. For a sevenfold triple, all thirteen outside points occur among its fourteen outside incidences; its unique repeated count is therefore exactly two.

These are necessary conditions for full regular covers. Their application while holes are allowed is an explicit partial-construction restriction. The independent derivation and its qualifications are recorded in `regular-heavy-hub-bound/README.md`.

## Exact selected-hub encoding

For each selected triple T and point p outside it, let q be the number of selected blocks containing T together with p. The new Boolean h has these five rows:

- h <= heavy6(T).
- q >= 2 when h is true.
- q <= 1 when heavy6(T) is true and h is false.
- q <= 3 when heavy6(T) is true.
- q <= 2 when heavy7(T) is true.

The first three rows give the exact equivalence h = (heavy6(T) and q >= 2). Each selected triple has at most one hub. For every point p, the sum of every heavy6 flag whose triple contains p and all selected hub flags at p is at most one. Unselected heavy triples enter the anchor side of these rows; their repeated hubs are not enumerated.

There are exactly 52 new Booleans and 280 rows: 260 local rows, four per-triple caps, and sixteen point-packing rows. The supplied base model grows from 6,428 variables and 7,254 rows to 6,480 variables and 7,534 rows. Every previous field, including the objective, complete hint prefix, and two allowed-assignment tables, is preserved.

## Hint and controls

The seed is the normalized nine-hole candidate with canonical SHA256 `ffe4fd80e9080522d790154394f1e8f55ca3c7ae2e5da3ce48ea99ba20cc26f3`. Both cover verifiers confirm 64 distinct regular blocks and nine holes. Direct triple and quadruple counts set only three selected hub flags: 123 at point 4, 7-10-13 at point 12, and 8-9-14 at point 15. The exact-six triple 5-11-16 has no repeated hub.

Every one of the 6,480 complete hint values and every active model row is checked without a solver. Focused tests reconstruct all 280 rows, compare every prior protobuf field, recount all 52 auxiliary values, exercise 104 local truth assignments, and reject damaged ordering, domains, heavy-flag implications, and selections. The independent review in `selected-heavy-hubs-independent/` separately checks the saved model, 208 local cases, and eleven damaged controls, including omission of an unselected heavy-anchor term.

The bounded pilot uses the existing relaxed first-family, residual, heavy-count, and normalized-hub model, then adds these selected-hub cuts. Its seed is 2026102801, budget 300 seconds, and worker count four. The run's model, logs, source snapshots, and metadata are saved in ignored scratch at `selected-heavy-hubs-h9-20261003`. Solver timeouts are inconclusive, and a solver negative alone is not an independently checked theorem.

The pilot finished `FEASIBLE` after 300.090946 seconds, returning the nine-hole seed at 0.971666 seconds and no improvement. Both verifiers agreed on that candidate. No full cover was found. `pilot.json.gz` preserves the complete metadata, frozen sources, result, witness, solver parameters, and every artifact hash; `pilot-manifest.json` records the archive hash. The full model and solver log remain in ignored scratch. This bounded optimization did not establish an impossibility result.
