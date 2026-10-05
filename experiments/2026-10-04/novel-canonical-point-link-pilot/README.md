```
Document:    New Local Witnesses beyond the Four Chosen Point Links
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      26acc36726eb5004ac268fb5f814ec07508279f20d04e94c475334abcfb74074
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

These four bounded local searches seek a twenty-K4 witness outside every
audited excess-graph automorphism image of the old chosen witness for its
class. A new local witness could broaden the constructive catalog. This is
a restricted witness search, not a completeness claim or a global exclusion.
Root alone launches the four calls after independent review. Preparation
uses no optimizer.

## Exact models

Each model uses all 1365 binary quadruple variables on labels 1..15 in
lexicographic order. It imposes all 105 exact pair demands of K15+E, using
the saved canonical class excess graph E, and fixes cardinality to twenty.
Every one of the 455 local triple rows has incidence at most one. This is
compatible with the triangle-free global pair recipe; the only triples that
could repeat under the pair rows are core triangles, whose global demand
is one.

For every independently audited old image F, add sum(y_R for R in F)<=19.
Since every chosen family has exactly twenty members, this excludes precisely
that old family, not its supersets or an unspecified equivalence class.
The old image catalog is already complete for automorphisms of each excess
graph applied to the one chosen witness. No objective, hint, symmetry break,
or other membership restriction is added.

| Case | Class | Old-image exclusions | Model rows | Solver seed | Seconds | Workers |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | C4-leaf | 96 | 657 | 2026106601 | 30 | 1 |
| 2 | C5 | 320 | 881 | 2026106602 | 30 | 1 |
| 3 | triangle-path2 | 96 | 657 | 2026106603 | 30 | 1 |
| 4 | triangle-two-leaves | 144 | 705 | 2026106604 | 30 | 1 |

Row order is the 105 lexicographic pairs, exact cardinality, 455 lexicographic
triple caps, then old images in their frozen catalog order. Preparation
checks first and last old images in each case against the complete model:
each violates exactly its own exclusion row and satisfies every other row.

## Bounded execution and evidence

The four calls are sequential, with a total solver allowance of 120 seconds.
Each child has a 35-second wall watchdog and five-second TERM grace before
KILL. The wrapper reuses the exact pinned, previously checked watchdog code
without modifying it. There is no retry, extension, or budget transfer. An
exclusive launch file and fresh output guards reject accidental reruns.

The seed audit includes ignored text artifacts. Model and parameter protos
live in ignored scratch; the manifest pins their hashes, the source revision,
Python and OR-Tools versions, old images, class data, representative map,
profile, verifier sources, and watchdog source. Logs, returned vectors,
result hashes, and watchdog outcomes are retained after any root launch.

Every feasible local witness is checked for twenty distinct integer-label
quadruples, all exact pair demands, all triple caps, and every old-image
exclusion. Both existing verifiers check the local pair cover with v=15,
k=4,t=2. The witness is then mapped through a saved actual point-one link
bijection and lifted to twenty pentads on labels 1..16. Both verifiers must
agree on 185 covered triples and 375 holes, and subtraction from the pinned
actual excess profile must leave nonnegative demands of total 440 with
every point-one triple row already satisfied. Only then is it reported as
an actual partial cover. It remains a partial, not a 64-block cover.

Prepare with `uv run python experiments/2026-10-04/novel-canonical-point-link-pilot/run.py prepare`.
After independent GO, root may replace `prepare` with `run` to launch once.
UNKNOWN and timeouts are inconclusive. CP-SAT INFEASIBLE is not an
independently checked theorem and carries no global implication.
