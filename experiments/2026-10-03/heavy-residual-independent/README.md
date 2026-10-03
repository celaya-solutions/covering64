```
Document:    Independent Combined Heavy and Residual Model Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      b52db76577ed10ab03c43ed2d5baec3905580f2ef6756a133b9be8954b4e63ab
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent combined model audit

The frozen `r4-005` heavy/residual model passes this independent audit. It has
6,428 variables and 6,929 constraints. All 6,428 saved hint values are checked;
the checker evaluates every saved constraint without invoking a solver.

The checker independently reconstructs all 1,105 residual rows and all 2,817
heavy rows from the lexicographic block universe. It checks all 364 residual
variables, 1,120 heavy variables, and their derived hints. Residual rows precede
heavy rows in this saved model. The 16 local auxiliary hints are independently
recounted from the candidate. Frozen source snapshots are hash-checked evidence,
not the mathematical oracle.

The heavy-row checks cover the multiplicity cap of seven, both directions of
each threshold flag, pointwise heavy-triple disjointness, and the weighted count
bound. A 316-case truth table checks threshold semantics. Eighteen damaged
controls cover altered model rows, auxiliary hints, ignored partial holes, and
malformed witnesses.

The normalized escape witness has 64 distinct blocks, point degrees 20, six
uncovered triples, and four pairwise disjoint sevenfold triples. Both verifiers
agree. Its point-map image is checked against the saved source witness, and its
local families are identical to the normalized h5 seed. Their full-completion
hub row is `[3,2,1,1,2,2,2,3,2,2,3,2]`, summing to 25 against budget 24. Thus a
full completion in this regular branch must change at least one local family;
changing only the 18 outside blocks cannot succeed.

This audits a restricted partial-construction model and its saved feasible
hint. It proves neither existence nor global nonexistence of a 64-block cover.
The heavy cuts are full-cover consequences used as additional restrictions on
partial search. Partial residual rows correctly exclude the actual global holes.

Reproduce from the worktree root:

```sh
uv run python experiments/2026-10-03/heavy-residual-independent/check.py
```

Model SHA256: `a4e914f8de6eb39b3c2872e3db27cff70b22391641958206a639d330f28b3b14`.
The large model and frozen source snapshots remain in the ignored scratch run
`first-family-hint-r4-005-heavy-residual-20261003`. The result records their hashes,
verifier hashes, solver version, and checker hash. The earlier residual-only
audit is unchanged.

A separate raw subset recount in `hub-profile.json` finds repeated hubs
`4,4,12,15` for the four sevenfold triples, respectively. The first two reuse
hub 4. In a full regular 64-block cover, each point has five pair-excess units,
while serving as the repeated hub of a sevenfold triple consumes at least
three. Two such roles would consume six, so the hubs must be distinct. This
partial witness therefore fails another known necessary condition even though
it passes the count and disjointness filters in the saved model. Its eligibility
must always be stated relative to those tested filters.
