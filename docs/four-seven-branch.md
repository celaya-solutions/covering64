```
Document:    The Regular Four-Sevenfold-Triple Branch
Version:     v1.3.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      0eaeafaece888d346150f0c3bff6f6826a96457b169637b6f3af3737007ea012
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Scope

This reduction applies to a full cover of all triples on 16 points by 64 distinct
5-subsets, with point degree 20 and four triples of multiplicity seven. It does
not cover the degree-19 branch or regular covers with fewer sevenfold triples.
There is no new 64-block covering witness at this checkpoint.

The earlier checked heavy-triple and hub restrictions imply that the four
triples are disjoint and have four distinct hubs outside every heavy triple.
Thus they partition the points into four groups:

| Group | Anchor triple | Hub |
|---|---|---|
| 1 | 1, 2, 3 | 4 |
| 2 | 5, 6, 7 | 8 |
| 3 | 9, 10, 11 | 12 |
| 4 | 13, 14, 15 | 16 |

This simultaneous relabeling is safe. It does not justify imposing any further
normalization of a seven-block link.

# Forced pair counts

Every pair occurs at least five times: its blocks cover 14 third points, at
most three per block. A degree-20 point has pair-count sum 80, leaving an excess
of five over the 15 baseline counts of five.

For an anchor point, its two internal pairs have count at least seven, and its
own-hub pair has count at least six by the checked sevenfold link argument.
These spend all five excess units. Therefore the internal pair counts are
exactly seven, the own-hub count is exactly six, and all other pairs at an
anchor have count five.

Each hub spends three excess units on its own three anchors. Its other anchor
pairs have count five, leaving exactly two excess units among the other hubs.
The hub excess graph is a loopless multigraph of weighted degree two on four
vertices. There are six labeled possibilities: three 4-cycles and three pairs
of doubled matching edges. Simultaneously permuting the four groups reduces
these to two cases.

| Case | Hub pairs above baseline five | Counts of pairs at multiplicities 5 / 6 / 7 |
|---|---|---|
| cycle | +1 on 4–8, 8–12, 12–16, 4–16 | 92 / 16 / 12 |
| matching | +2 on 4–8 and 12–16 | 94 / 12 / 14 |

Both cases have pair-count sum 640 and pair-count sum 80 at every point.

# Allowed blocks and triple counts

An internal anchor pair has its entire count of seven supplied by blocks
containing its complete anchor triple. Hence no block contains exactly two
anchors from a group.

There are 1,476 allowed blocks. Of these, 276 contain an anchor triple:
four choices of triple and 69 allowed outside pairs. The other 1,200 contain
at most one anchor per group. Their counts by number of hubs are 324, 648,
216, and 12 for one, two, three, and four hubs respectively.

Exactly 28 selected blocks contain an anchor triple, leaving 36 other blocks.
In the 28 heavy blocks, each anchor has degree ten and each hub degree five.
Thus the other 36 blocks give each anchor degree ten and each hub degree 15.

Every nonheavy triple has multiplicity one or two. Except for a triple
consisting of two anchors and their own hub, it contains a pair of multiplicity
five: the 14 triples through such a pair have total count 15, so no one can
exceed two. A triple consisting of two anchors and their own hub occurs exactly
twice in its heavy link. Consequently the full multiplicity profile is four
triples of multiplicity seven, 56 of multiplicity two, and 500 of multiplicity
one. This is a necessary profile, not a construction.

The location of the repeated outside point uses integrality. Write d for the
number of heavy-link blocks containing an outside point other than the named
hub. For any anchor, its pair with this outside point has count five. Two of
the 14 triples through that pair each occur d times, and the other 12 occur
at least once. Thus 2d + 12 <= 15. Since d is an integer and coverage requires
d >= 1, d = 1. The seven link edges have 14 endpoints on 13 outside points,
so the named hub has degree two. This fixes 144 two-anchor triples to count
one and the 12 own-hub triples to count two. A fractional model can have
1 < d <= 3/2 and does not get these equalities from the same argument.

# Implementation and evidence

`scripts/four_seven_search.py` retains all 4,368 block variables in the package's
lexicographic order. It fixes the 2,892 disallowed variables to zero and adds
64-block size, point-degree, pair-count, four anchor-count, and all triple
coverage constraints. Each full model has 4,368 variables and 3,593 rows.
There are no assumptions about the shape of a particular heavy link.

The independent checker in
`experiments/2026-10-03/four-seven-independent/` reconstructs every variable and
row for both cases. It also checks all six hub graphs, their two orbits, the
allowed-block counts, damaged model controls, and damaged candidate controls.

The optional partial mode retains these full-cover branch restrictions and
minimizes missing triples. A partial result cannot establish that the branch
contains a cover. Every emitted candidate must pass the branch recount,
package verifier, and separate standalone verifier.

The initial two exact searches each used 300 seconds and four workers. Both
returned UNKNOWN without a candidate. Two later searches with explicit double
variables also returned UNKNOWN after 300 seconds each. Exact rational witnesses show that the
original linear relaxations are feasible (denominators dividing 36 for the
cycle case and 162 for the matching case). These fractional witnesses are not
covers. In particular, the exact locations of the 156 fixed two-anchor triple
counts use integrality in the hub proof. The saved rational witnesses happen
to satisfy these equalities too, and extend to all 400 double variables. The
lifted model has 4,768 variables and 4,270 rows, all independently reconstructed.

Two separate necessary 44-triple systems have integer solutions, each checked
directly against all pair demands. They are not block covers. Fixing these
double patterns in the block model gave one 120-second UNKNOWN and one solver
INFEASIBLE result without an independently checked integer certificate.

The optional group-symmetry pilots are only construction subcases. A cycle of
the four groups in the cycle case, and the specified Klein-four action in the
matching case, both contain a fixed-point-free involution on points. Every
5-subset therefore has an orbit of size two under that involution. A swapped
cross-anchor pair is fixed as a set and must consequently occur an even number
of times, contradicting its required multiplicity five. An independent checker
replayed all 4,368 blocks and both parity certificates. This excludes those two
explicit actions, not the full branch or every possible automorphism.

# First-link classification and linear screens

The first heavy triple's seven blocks consist of that triple plus seven edges
on the 13 outside points. Hub 4 has degree two and the other 12 points have
degree one. The two edges at hub 4 form a two-edge star; the remaining ten points
form five disjoint edges. No edge lies inside another anchor triple.

There are exactly 29,970 labeled links. Inclusion-exclusion over the nine
forbidden edges gives 62,370 - 42,525 + 11,340 - 1,215 = 29,970. The forbidden
edges lie in three disjoint triangles, so at most one edge per triangle can be
part of a matching. An independent direct enumerator reaches the same count.

Permuting anchors within the other three groups and applying a hub-graph
permutation fixing the first group gives a group of size 432. Each of the two
pair-count cases has 129 link orbits. The independent audit checks group closure,
pair-count invariance, orbit completeness and disjointness, and all 59,940
recorded forward and inverse relabelings. Selecting one representative per
orbit is a complete label reduction within the stated branch. It does not
assume that a final cover is invariant under any of these permutations.

For each representative, the LP screen fixes its seven heavy blocks in the
audited lifted model. A numeric infeasibility report is not counted as an
exclusion. A phase-one LP keeps the base model hard and permits slack only in
the seven new fixed-block rows; this seeks certificate weights efficiently.

The certificate checker uses integer arithmetic. For each row weight it chooses
the lower bound when the weight is positive and the upper bound when negative.
Their weighted sum is a lower bound on the same weighted linear expression.
For variables between zero and one, the largest possible expression is the sum
of positive column coefficients. A strict gap between these bounds is a proof
for that fixed-link model. No claim depends on numerical solver optimality.

All six positive certificates in the ten-representative pilot passed a separate
checker reading frozen raw model rows. The complete 258-representative screen
then excluded 27 cycle representatives and 73 matching representatives. All
100 certificates passed independent exact arithmetic checks against 4,768
columns and 4,277 rows each. The other 102 cycle and 56 matching representatives
were numerically feasible in the LP relaxation and remain open as integer
covering cases. The full branch and the original 64-block problem remain open.

Large model files remain in ignored scratch directories. Their source snapshots,
model hashes, solver version, seeds, parameters, logs, and results are retained.
UNKNOWN is inconclusive. A solver INFEASIBLE result alone is not an independently
checked nonexistence theorem.

## Subsequent feature and odd-set screens

The first five feature rules and thirteen additional hull-facet families are
safe integer-cover consequences of the original 100 checked exclusions. Both
158-case screens stayed numerically feasible. The independently audited
8,096-row odd-set extension then gave checked exclusions for matching-038 and
matching-051, with positive exact gaps 8413/1000000 and 1007/200000. The
totals at that stage were 27 cycle and 75 matching exclusions, leaving 102 cycle and 54
matching cases open. See `four-seven-blossom-screen` and
`four-seven-blossom-independent` under the experiment directory.

The complete surviving-template hull formulation, frozen using only the
original 100 exclusions, was independently checked against every labeled
catalog member and every sparse marginal row. Its whole-branch LPs remain
numerically feasible. No result here proves a global bound or supplies a
64-block covering witness.

## Hub-count and full-template screens

The independent six-case hub-count campaign screened all 156 remaining first
links. Exactly one, matching-077, has a positive checked certificate in all six
cases. Later exact replay repaired all seven initially inconclusive numerical
subcases, bringing the conditional exclusion count to 419 of 936. This leaves
517 numerically LP-optimal conditional records; it adds no other complete
first-link exclusion.

The complete template-hull screen excluded matching-017, matching-077 and
matching-083. Each certificate was independently replayed over 61,576 unit-box
columns and 4,557 rows, with the frozen hull encoding separately audited.
Their respective positive gaps are 1193423/1000000000, 161/1000000 and
19029/1000000. The matching-077 exclusion overlaps the hub campaign.

The union is therefore **106 distinct checked exclusions: 27 cycle and 78
matching**. The remaining **152 cases: 102 cycle and 50 matching** are open.
All numerical witnesses from the full-template screen remain fractional.
Compact proof archives and the checked union inventory are in
`four-seven-template-link-independent`; hub evidence and numerical repair
replays are in `four-seven-hub-count-screen` under the dated experiment folder.

The combined-template priority screen tested the last open hub-count subcase
for each of 23 first-link representatives. It produced one new independently
replayed certificate: matching-032 at (m4,z)=(0,1), gap 7651/1000000. Together
with its five previously checked hub cases, this excludes matching-032 entirely
within the regular four-sevenfold branch. The 22 other priority LPs remain
numerically optimal and fractional. This brings the combined total to 106
excluded first links and 152 open; it supplies no covering witness.
