```
Document:    Classification of Regular Thirteen-Point Local Families
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      cdc5b4ba6a3f8f338ac9b772569fd2befb6602b88af8ed2a6861181ef5fc7e0e
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Scope and result

The finite enumeration classifies families of 13 distinct quadruples on 13
points, with every point in four quadruples, whose missing pairs form a
matching. There are exactly three isomorphism classes in this scope: the
projective plane of order three, a family with four missing pairs, and a family
with six missing pairs. Here isomorphism permits every point permutation and
every block permutation; no point or block is marked.

This is a classification of local families, not a construction or exclusion of
a 64-block C(16,5,3) covering. Its relevance to a regular covering with a triple
of multiplicity seven uses the separately checked no-both-spokes obstruction
in `../thirteen-point-links/`. That result forces the local missing graph,
initially a subgraph of P3 plus five independent edges, to be a matching.

The six-hole class is isomorphic to the previously found spoke counterexample.
The four-hole class supplies an additional valid constructive search input.
Its missing pairs, with the labels in `enumeration-family-001.txt`, are
(5,12), (6,9), (7,10), (8,11). The other five points are unmatched.

# Complete reduction

Let H be the missing-pair graph and let lambda(x,y) count blocks containing
both points. At each point, four blocks contribute 12 pair incidences. There
are also exactly 12 other points. Therefore the positive pair excess at a
point equals its degree in H. Because H is a matching, every positive excess
is one, and the repeated pairs form a matching F on exactly the endpoints of
H, disjoint from H. There are at most six missing pairs.

Choose a point q outside H. Such a point exists because 13 is odd. Its positive
excess is zero, so every pair through q occurs exactly once. The four blocks
through q consequently partition the other twelve points into four triples.
Relabel q as 13 and these four triples as {1,2,3}, {4,5,6}, {7,8,9}, and
{10,11,12}. This normalization is available for every family in scope.

No H edge lies within one triple because the corresponding q-block already
covers that pair. Record the number x_ij of H edges between each pair of
triples. These six nonnegative integers have degree at most three at every
triple. Conversely, every such vector defines a realizable matching between
the triples. Two matchings with the same vector differ only by permutations
within the four triples: their endpoints are distinct, so the required
endpoint bijections extend separately inside each triple. Permuting the four
triples acts as S4 on the vector. Enumerating all 4^6 vectors, retaining those
with degree at most three, and taking the least vector under S4 is exhaustive.
The numbers of types for 0,1,2,3,4,5,6 holes are 1,1,3,6,7,5,3: 26 in total.

Exactly nine blocks remain. They avoid q, each of the twelve points occurs
three times, no block contains an H edge, and every other pair must be covered
after including the four fixed q-blocks. These are finite conditions on the
495 possible quadruples on twelve points.

# Two enumeration methods

`enumerate.py` enumerates every F on the endpoints of H, disjoint from H. The
union H plus F is a disjoint union of alternating even cycles. As an optional
necessary filter, it computes the exact determinant of the 13 by 13 Gram
matrix with diagonal four and off-diagonal 1 + F - H. This determinant must
be the square of the integer determinant of the incidence matrix. The allowed
cycle half-length partitions are: no cycles for zero holes; (3) for three
holes; (2,2) for four holes; (5) for five holes; and (2,4) or (3,3) for six
holes. The numbers of labelled F surviving for hole counts 0 through 6 are
1,0,0,8,12,384,2080. It quotients colored (triple groups,H,F) graphs with nauty,
then enumerates exact K4 decompositions of the residual pair multiplicities.
The recursion chooses an unsatisfied pair and chooses all required blocks
through that pair at once, so every exact decomposition is considered.

`replay.cpp` independently generates all 26 H types and searches directly for
the nine remaining quadruples. It uses no determinant filter, no F enumeration,
no nauty calls, and no quotient after H normalization. It starts with each
within-triple pair covered once by its q-block. Every added block must keep
each point's residual degree at most three and its positive pair excess at
most its degree in H. These conditions are necessary by the preceding counting
identity. It branches on an uncovered non-H pair and considers every currently
legal block through it. Any completion must contain one of these blocks.
If all pairs are covered before nine blocks, no additional legal block exists:
every pair in that block would be a repeated pair, giving excess three at its
points, whereas their excess bounds are at most one. Completed block sets are
deduplicated without discarding search branches.

Both methods terminate completely. The Python run uses 4,933 recursive nodes.
The direct C++ run uses 4,197 nodes and returns these 88 labelled completions:

| Hole vector (12,13,14,23,24,34) | Holes | Labelled completions |
|---|---:|---:|
| (0,0,0,0,0,0) | 0 | 72 |
| (0,0,0,1,1,2) | 4 | 6 |
| (0,0,2,2,0,0) | 4 | 2 |
| (1,1,1,1,1,1) | 6 | 8 |

The other 22 hole vectors have no completions. The eight four-hole completions
belong to one unmarked isomorphism class. The eight six-hole completions also
belong to one class. `check_replay.py` checks every returned family by direct
pair counting, the package verifier, and the separate standalone verifier. It
also compares all unmarked incidence-graph certificates against the three
Python representatives and rejects six damaged controls. The pair verifiers
report `valid: false` for the partial four-hole and six-hole families; their
exact missing-pair lists are the intended result. None is presented as a full
pair cover.

# Reproduction

From the repository root:

```sh
uv run --with pynauty==2.8.8.1 python experiments/2026-10-03/local-family-classification/enumerate.py --seconds 60 --output experiments/2026-10-03/local-family-classification/enumeration.json
c++ -std=c++17 -O3 -Wall -Wextra -pedantic experiments/2026-10-03/local-family-classification/replay.cpp -o /tmp/covering64-local-family-replay
/tmp/covering64-local-family-replay 60 > experiments/2026-10-03/local-family-classification/replay.json
uv run --with pynauty==2.8.8.1 python experiments/2026-10-03/local-family-classification/check_replay.py
```

The enumerations are deterministic and do not use random seeds or a SAT/CP
solver. Each has a 60-second budget. A time-limited run reports incomplete and
does not certify classification. Source revisions, source/input hashes,
runtime versions, compiler flags, and sanitizer results are retained in the
JSON artifacts. Raw witnesses intentionally contain only one-based labels.
