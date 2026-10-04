```
Document:    Hub-Unrestricted Fixed-Heavy Completion Diagnostic
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      8a08f0ff68a3ec289bf22c130bbeefbf8ace2abf438af11eaf0b7d5f07d80795
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Fixed-heavy completion with all hub pair patterns allowed

The audited native pilot state has 64 distinct blocks and ten uncovered triples.
Its 28 heavy blocks are fixed as constants. The completion model selects exactly
36 of all 1,200 legal ordinary blocks, in original lexicographic block order.
Point labels stay 1-based; variable names retain original zero-based global IDs.

There are 577 linear constraints: one cardinality equality, all 560 triple
coverage rows, and 16 point-degree equalities. Heavy incidence is subtracted
from each right-hand side. The 160 empty-support triple rows are explicit empty
linear rows. There are no pair rows, hub graph constraints, hints or objective.

Each satisfying assignment gives precisely the fixed heavy blocks plus 36
distinct ordinary blocks, covers every triple, and has degree 20 at every point.
Conversely, every completion in this fixed-heavy, native ordinary-block family
satisfies these rows. This is not an unrestricted 4,368-block model.

## Independent gate and pilot

The independent checker in `../native-ten-hole-completion-independent/`
reconstructed all 1,200 variable identities and all 577 rows without importing
the builder. It rejected six damaged model controls. The checked model SHA256
is `0f2148c72e8c1af5ae88e5842e630f00201934d3f059d5238fff00828d647257`.
An initial export with equivalent Boolean tautologies for empty rows is saved
only in the ignored `lookahead-heavy-completion-v1.0.0-draft` directory. It was
not used for the gated pilot.

One CP-SAT diagnostic ran with OR-Tools 9.15.6755, seed 2026104401,
a 60-second native limit and one worker. It returned **UNKNOWN** with no witness:
60.002758 seconds native time, 60.502904 seconds wrapper time, exit 0, empty
stderr and no forced termination. UNKNOWN is inconclusive. This does not exclude
the heavy tuple or any first-link representative and changes no bound.

Raw model, source snapshots, gate, parameters, response and full logs are saved
under ignored `experiments/scratch/lookahead-heavy-completion-v1.0.0` and
`experiments/scratch/lookahead-heavy-completion-pilot-v1.0.0`. Compact source,
manifest, seed and result remain here. No further run is implied.

## Independent state recount

`check_seed.py` uses the previously checked independent oracle to recount all
1,200 ordinary candidates for the final native pilot best. The complete set of
680 admissible candidates and the empty unsupported-triple set match the saved
native sidecar. The seed has degree 20 at all points and exactly ten uncovered
triples; it is not a covering witness. See `seed-audit.json`.

## Brief affine-builder review

A separate read-only review of `../affine-extension-completion/build.py` found
no defect. The finite circles and 240 line extensions are disjoint. Fresh checks
for zero, three and all 48 deleted circles confirmed the exact extension count,
missing-triple sets and row counts. Builder SHA256 is
`9aaf86673b4d8eb3aa8e91fde1d7f5e84acc409454314e2f063ffea47542e8a4`;
the current pool SHA256 is
`913c47b15b1783472bf5c1a97e616a13504db7ee2b49d19804154d4b52724729`.
This brief review did not repeat the primary 22-case preflight or run a solver.
