```
Document:    Exact Fractional Witnesses for the Four Sevenfold Branch
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      468af07b51c0cb75bda8f0b2b1401323cb23d830370a66922ef56d0fa08fbc21
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

Both original linear relaxations are feasible. Exact rational witnesses are saved for the cycle and doubled-matching hub-pair cases. Every one of the 4,368 continuous variable domains and 3,593 original rows is checked with rational arithmetic, independently of the numerical solver. Cycle weights have denominators dividing 36; matching weights have denominators dividing 162. Damaging one weight makes the exact check fail. These are fractional vectors with total block weight 64, not integral covers.

The numerical full LPs were solved with GLOP. Tying equivalent blocks under independent anchor permutations and hub-pattern automorphisms gave simpler rational solutions. The latter models have 52 orbit variables. Averaging preserves a feasible LP because each permutation preserves the original model and the feasible set is convex. More importantly, the saved full vectors are checked directly against every original row; their certificate does not depend on numerical optimality or the symmetry reduction.

The anchor groups are 123, 567, 9-10-11, and 13-14-15, with respective hubs 4, 8, 12, and 16. The cycle hub-pair excess uses edges 4-8, 8-12, 12-16, and 4-16; the matching uses doubled edges 4-8 and 12-16. All labels are one-based, while witness indices are zero-based positions in the global lexicographic block list.

## Integer-derived double-triple lift

In an integral full cover, each sevenfold anchor triple has fourteen outside incidences covering thirteen outside points. Exactly one outside point occurs twice. The prescribed pair counts identify that point as its own hub: any repeated point would force pair multiplicity at least six to all three anchors, and every other outside point has pair multiplicity five to those anchors. Therefore the 156 triples containing exactly two anchors from one group have fixed multiplicities: twelve own-hub triples have count two, and the other 144 have count one.

The remaining 400 triples have at most one anchor from each group. Every such triple contains a pair of multiplicity five; for three hubs this uses the triangle-free cycle or matching pattern. For that pair, its fourteen triple counts sum to fifteen and each is at least one, so the selected triple count is at most two. Consequently its count is exactly `1 + d`, with Boolean d. Summing all triple incidences gives `sum(d) = 640 - 4*7 - 12*2 - 144 - 400 = 44`.

The pair equations for these 400 flags require zero on internal anchor pairs, two on anchor-own-hub pairs, one on other pairs touching an anchor, and `3*lambda - 14` on hub pairs. They also follow by subtracting all fixed triple contributions and one base incidence per eligible triple from the total `3*lambda`.

`scripts/four_seven_double_cuts.py` adds exactly 400 flags and 677 rows: 400 links, 156 fixed counts, one total-44 row, and 120 pair equations. The twelve internal pair equations are explicit linear `0 = 0` controls. It requires the full-cover branch, including unconditional coverage, and refuses partial models. Every prior model field remains unchanged.

The fixed locations of the twelve double triples use integrality; they must not be assumed to follow from the original LP. In this experiment both specific saved rational witnesses happen to satisfy all 156 fixed rows. Their 400 fractional `d = count - 1` values then satisfy every new pair equation and sum exactly to 44. The saved extensions pass all 4,768 domains and 4,270 rows, and both strengthened GLOP models are feasible. Thus these strengthened LPs also yield no infeasibility certificate. Fractional double values are LP witness extensions and must not be supplied as integer CP-SAT hints.

## Evidence and replay

`check.py` records the original models, numerical solves, symmetry maps, and exact witness checks. `strengthened.py` loads those preserved original models and checks the double-triple extensions. The JSON witnesses, fixed-row checks, auxiliary values, and result files are durable. Full protobuf models, floating solutions, and MPS exports remain in ignored scratch under `four-seven-lp-20261003`; hashes are recorded in the manifests.

Focused tests reconstruct all 677 new rows, derive pair demands from independent incidence subtraction, preserve the full original protobuf, check both fractional extensions, and reject wrong cases, variable order, missing full coverage, duplicate application, and damaged fractional weights. A separate raw recount of both original witnesses is saved in `four-seven-independent/original-lp-recount.json`.

This evidence shows arithmetic consistency of the stated branch and its relaxations. It neither constructs a 64-block cover nor proves that an integral cover exists.
