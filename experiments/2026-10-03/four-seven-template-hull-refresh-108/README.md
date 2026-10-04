```text
Document:    Immutable Template-Hull Refinement from 108 Checked Exclusions
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      eb2a5cd3687361f6896bb8508daacfcfe98e60b4488785dc04aea99574e45036
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Second immutable template refinement

This version starts from the frozen 106-exclusion catalog and removes the two
new independently checked orbits. `matching-095` removes 216 labeled templates
per heavy group; `matching-113` removes 432. The additional reduction is 648
per group, or 2,592 template-weight columns over all four groups.

| Case | Templates per group before | Templates per group now | Variables now | Rows |
| --- | ---: | ---: | ---: | ---: |
| Cycle | 25,020 | 25,020 | 104,848 | 4,550 |
| Matching | 12,690 | 12,042 | 52,936 | 4,550 |

There are 102 surviving cycle orbits and 48 surviving matching orbits. The
checked union has 108 exclusions and 150 open first-link types. Cycle catalog
and matrix files remain byte-identical. No cycle-only LP is rescreened.

The builder removes only the two newly excluded orbit families, preserves
lexicographic survivor order, and reindexes only template columns. All 4,270
original rows and all 4,768 block/double columns remain unchanged. The 280 hull
row meanings and all transport permutations are preserved. Each template has
one simplex incidence and seven marginal incidences. Every retained template is
transported to all four groups with an inverse check; both alternative hub-graph
automorphisms give the same complete transported set for each group.

Completeness follows from the existing full orbit classification and checked
exclusion chain. Any normalized regular integer cover supplies one labeled
heavy-link template in each group. Moving that group to the first group by a
hub-graph automorphism cannot produce an excluded orbit. Its template therefore
remains in the new complete catalog, and assigning one unit selector weight to
it satisfies the corresponding hull equalities. No automorphism invariance of
the cover is assumed. The two new exclusions were proved on the older, larger
106-version hull, so this refinement introduces no circular proof dependency.

## Frozen provenance

- Predecessor manifest SHA-256: `84183ee44ed2916ffd18d64b5f113774e4eda47bad5e82c6c79b1b3a64db5bdf`.
- Checked 108-ID union: `../four-seven-template-hull-refresh-independent/combined-first-link-exclusions.json`.
- Union SHA-256: `2809b2f39fac1971ca6bf3997e789a4a41463b62394e7525e5d282d084527f88`.
- New manifest SHA-256: `dcbdfd83d9c1952fbcbc0e2e192897ce96fae126aa0d527011ca6f0e13eb8c87`.
- Builder SHA-256: `31734e4d2b927bc0933529d26addce16132ef9db8ef4a282af530b93d897cedb`.
- Matching catalog SHA-256: `3679c8c65b31985fc5d7d26e18ba5216aa6c6ee9f4941bd18cbf77d33fa56eb6`.
- Matching matrix SHA-256: `e9b2289291479c5f1119f432f0131d8fda8130ace2e64c773cf93dd8928ceade`.
- Raw output: `experiments/scratch/four-seven-template-hull-refresh-108-20261003/`.

The new build took 6.660 wall seconds. It preserves source, full exclusion union,
base catalogs, all four transported catalogs, matrices, input hashes and source
revision. No 106-version source, catalog, matrix, result or integer pilot is
changed. The large data stays outside Git.

## Next bounded screen and audit gate

Root independently audits the new union, complete labeled survivors, all
transports, matrix rows and damaged controls before any Solve call. A separate
new no-solve preflight then checks the matching solver layouts against this
exact matrix, including all 48 fixed/reset transitions in both feasibility and
phase I. The planned screen is the whole matching branch plus 48 first links,
at most 15 total solver seconds per case: a 735 solver-second ceiling, excluding
construction, checks, integer certificate arithmetic and file writing.

Each later refinement requires newly replayed exact exclusions and a fresh
immutable catalog with an independent audit. Stop the LP-pruning iteration when
a full refreshed screen yields no new checked exclusions, or when a candidate
passes both covering verifiers. Numerical feasible solutions and timeouts are
not exact covers or proofs. The regular branch and unrestricted covering number
remain unresolved at the time this catalog is constructed.
