```
Document:    Seven Conditional Affine Link Completion Pilots
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      4699f78eaf7a5c4012e1e5d5353de1dab07a4215719deaedca5e3f67af761f38
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

These seven prepared pilots seek a 64-block cover only within seven named
conditional branches. Each branch fixes a twenty-pentad affine point link and
its entire recipe excess profile. They are the seven survivors of the finite
support screen; survival does not imply a completion exists. No production
optimizer is called during preparation. Root owns the eventual launch after
independent model and runtime-wrapper approval.

## Model and bounds

Each model has all 4368 binary five-block variables in global lexicographic
order, with zero-based IDs. For each of all 560 triples, its incidence sum is
exactly 1 plus its membership indicator in the pinned 80-triple excess
profile. One row fixes total cardinality to 64. Each of the 1365 variables
whose block contains the selected point is fixed: the twenty pinned partial
blocks have value one, and the other 1345 have value zero. All 3003 blocks
avoiding that point remain free initially. There are 1926 rows in total.

No objective, hint, extra symmetry assumption, or support-propagation pruning
is added. The derived zero-residual triples follow from the exact global rows
and pinned memberships. The saved 455-row residual lists are audit evidence,
not additional model restrictions. Total remaining demand is 440 and forces
44 further blocks. Each actual twenty-block partial is supplied with its
canonical hash and checked by both existing cover verifiers. The expected
partial result is 185 covered triples and 375 holes.

| Case | Profile seed | Point | Solver seed | Seconds | Workers |
| --- | --- | --- | --- | --- | --- |
| 1 | 0 | 10 | 2026106301 | 30 | 1 |
| 2 | 40 | 13 | 2026106302 | 30 | 1 |
| 3 | 4 | 7 | 2026106303 | 30 | 1 |
| 4 | 18 | 3 | 2026106304 | 30 | 1 |
| 5 | 16 | 3 | 2026106305 | 30 | 1 |
| 6 | 16 | 8 | 2026106306 | 30 | 1 |
| 7 | 60 | 3 | 2026106307 | 30 | 1 |

The seven calls run sequentially. Each child has a 35-second wall-clock
watchdog; the parent sends its process group TERM and allows five seconds
before KILL. There is no retry, extension, or transfer of unused solver
budget. The total solver allowance is 210 seconds. An exclusive launch
record and fresh output directories reject accidental reruns.

## Preparation and eventual root launch

Preparation is `uv run python experiments/2026-10-04/clebsch-affine-link-completion-pilot/run.py prepare`.
It writes raw model and parameter protos under ignored scratch, actual partials,
profile copies, residual rows, both verifier receipts, and a manifest pinning
all inputs, source revision, runtime versions, rows, parameters, and files.
The seed audit searched tracked and ignored text artifacts for prior usage.

After an independent GO, root may use the same command with `run` instead of
`prepare`. The root wrapper records each child exit, watchdog action, raw log
hashes, and result hash. A feasible result is accepted only after checking
every exact profile row, every fixed membership, exact 64-block cardinality,
and both full-cover verifiers. The complete solution vector and explicit
witness are saved. UNKNOWN and timeouts are inconclusive. CP-SAT INFEASIBLE
is not an independently checked theorem and cannot exclude other links or
profiles, much less unrestricted existence.
