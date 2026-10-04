```text
Document:    Independent Complete Sweep and Dual Envelope Audit
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      6ffe60e668e76c448c6fcbf99aa40bed11fb1875db9d71445063a361c03ede7e
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

This folder contains pure combinatorial and exact-arithmetic checks. None of its
scripts creates a solver or requests a solve. The scope is the fixed-anchor
regular four-sevenfold family, including all six allowed hub graphs. It makes no
global lower-bound claim and supplies no 64-block covering witness.

`basis.py` independently rebuilds the 4,368 lexicographic global blocks, 1,200
ordinary blocks, 276 heavy blocks, and 697 unconditional rows. `check.py` gates
the frozen 136-neighbor sweep. `postcheck.py` reads its completed result, binds
every tuple and shifted row set, recomputes every saved primal residual, and
checks all 113 fresh dual vectors. There are 23 cached and 113 fresh OPTIMAL
reports. The smallest recomputed neighbor residual is 5.644705064340972; the
unchanged incumbent's numerical objective is 5.575882992498541. This numerical
comparison alone is not an exact local-optimality certificate.

`bundle_check.py` independently reconstructs all 113 saved support planes by
summing each column's row supports. It verifies exact ordering, certificate and
source hashes, integer weights with absolute value at most D = 1,000,000, and
zero negative weights on infinite-upper rows. For signed row weights w, let c
sum w times the lower bound when w is positive and the upper bound otherwise.
Let a and b be the resulting ordinary and heavy column sums, and let
q = sum(max(0, a_j)). Then

    (c - q - b·h) / D <= total elastic L1 residual

for every ordinary vector in [0,1]^1200. Each signed row term is at most D times
its corresponding violated side; a·x is at most q. This proof uses exact
integers and needs neither numerical dual feasibility nor numerical optimality.
The maximum of these planes and zero remains a valid lower bound.

The saved incumbent ordinary vector is converted from each binary float to its
exact rational value and clamped to [0,1] (zero entries needed clamping). Its
exact row residual is 25714221636893855419 / 4611686018427387904, a valid upper
bound for incumbent comparison. All 136 neighbors have positive exact envelope
bounds, the smallest being 362507/500000. Thus all 136 fixed heavy tuples have
no fractional completion in this family. Only 116 bounds reach the exact
incumbent upper bound, so exact objective pruning and exact feasibility
exclusion are different claims. The incumbent envelope value is
3429927/1000000.

`larger_moves.py` enumerates all endpoint-degree-preserving replacements of three
edges in one anchor link and pairs of two-edge replacements in distinct links.
Proper replacements change every selected outgoing edge. It checks the heavy
universe before applying the joint global nonanchor-triple cap. In particular,
constituent two-edge switches are not discarded for failing the individual cap
before they are paired. It checks tuple uniqueness and scores the exact same
113-plane envelope without optimization.

| Neighborhood | Raw | In heavy universe | Legal | Positive exact bound | Bound reaches incumbent upper |
| --- | ---: | ---: | ---: | ---: | ---: |
| Proper three-edge | 980 | 660 | 660 | 657 | 477 |
| Paired two-anchor | 9,600 | 6,936 | 6,900 | 6,876 | 5,191 |

For each link, 30 three-edge subsets have six distinct endpoints, with eight
proper matchings each. The five subsets containing both hub edges and one
separate edge have one proper replacement each. Hence 30×8 + 5 = 245 raw
three-edge moves per anchor. Each anchor also has 40 raw proper two-edge moves;
34 use allowed heavy blocks. All 34 individually pass the cap for this tuple,
so there are zero jointly valid pairs requiring cancellation of an individually
invalid constituent. The joint cap rejects 36 of the 6,936 paired states.

The resulting finite feasibility fallback contains three three-edge states and
24 paired states whose envelope is zero. A zero bound is inconclusive. For
objective improvement, 183 and 1,709 states respectively remain unpruned. The
primary proposed escape strategy is the nearest-heavy lazy master; these counts
only describe finite alternatives and do not authorize a runner or new solves.

All full move lists and preliminary postchecker versions are in ignored
scratch. The canonical JSON receipts bind the final sources and evidence. The
initial gate and its receipt are unchanged. All files in this folder pass Ruff.

`intersect_cuts.py` subsequently replays all 333 planes from the finished
nearest-heavy campaign. Of the 27 zero-envelope finite neighbors, eight fail
the initial 238 cuts and all remaining 19 fail the final cuts. Seven were
directly evaluated by that campaign. No finite feasibility fallback remains.
All 333 row-weight norms were also checked against their certified denominator.
`max-margin-proposal.md` describes a distinct proposed objective; no runner or
optimizer was invoked for it.
