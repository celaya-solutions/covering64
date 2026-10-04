```text
Document:    Factorized Degree-Nineteen Overlap-Five Classification
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      108e0842537b95063b854af07bf91b4a8706166ddc40c47fd2c85a382dadfea4
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Scope and result

This is a factorized enumeration of pairs of degree-19 point links sharing
five blocks, conditional on the independently replayed four-class link
classification. It is a new subcase relative to the existing six-overlap
work. It assumes two selected degree-19 points and does not impose that
assumption on the entire covering problem. The adjacent degree19-roadmap
note gives the complete degree-19 split, including the sole-degree-19 case.

The factorization gives 34 first-link/second-anchor types and 34 source-link/
distinguished-vertex types. Each of the 1,156 type pairs has 10,368 compatible
shared-star maps. Thus 11,985,408 maps are represented by a compact exact
regeneration recipe. Quotienting source stabilizers gives 7,402,752 distinct
second links with the first type fixed. Quotienting target stabilizers as
well gives 4,578,210 classes of 33-block unions with ordered distinguished
anchors. Anchor reversal is not identified. These counts await the separate
independent factorization audit; no extension search has been run.

The millions of unions are not materialized or claimed as saved individual
files. `factorization.json.gz` contains the complete mapping group, every
source and target star, exact coordinate maps, full first and source links,
explicit source and target stabilizer elements, conjugacy data, all 1,156
count records, and four explicitly regenerated pilot unions.

# Why the shared-star shape is complete

Fix the first anchor as point 1 and a non-hub point `q` as the second
degree-19 anchor. A classified first link contains `q` in five quadruples.
Equivalently, the five common full blocks contain both anchors and give five
triples on the other 14 points. Triple coverage through the anchor pair
requires every one of those 14 points to occur. There are 15 incidences, so
one point occurs twice and the other thirteen occur once. The two triples
containing that repeated point meet only there; the remaining three triples
are mutually disjoint and disjoint from those two except for no points.
The implementation checks this exact incidence pattern for every type.

Assign coordinate 0 to the repeated point. Use `{1,2}` and `{3,4}` for the
other points in its two triples, and `{5,6,7}`, `{8,9,10}`, `{11,12,13}` for
the three isolated triples. Every star automorphism fixes 0, exchanges the
two intersecting triples or not, permutes their two private points, permutes
the three isolated triples, and permutes the points within each. Therefore
the full mapping group has order `2*2^2 * 3!*(3!)^3 = 10,368`. Every such map
is valid and no other map can preserve the repeated-point incidence pattern.

# Complete map and class enumeration

The first full link is one of the four classified links. Its verified full
automorphism group reduces the non-hub choice of `q` to 34 point orbits.
For the second link, the preimage of anchor 1 must be a degree-five vertex
in one of the same four classified links. Source automorphisms reduce that
choice to the same 34 orbit types. Picking an orbit representative loses
no image: compose any embedding with a source automorphism taking the
representative to the original distinguished vertex.

For a target type and source type, map the source distinguished vertex to
anchor 1. Canonical coordinates identify the remaining fourteen source and
target points with the shared-star coordinates. Every compatible embedding
then has the unique form

```text
source distinguished vertex -> 1
source coordinate i -> target coordinate g(i),  for g in G.
```

Mapping every source quadruple and adding `q` regenerates the second full
link. Exactly its five blocks through anchor 1 are the prescribed shared
blocks. It has no other intersection with the first link, whose blocks all
contain anchor 1. Hence the union contains exactly `19+19-5 = 33` blocks.

Let `K` be the source-link automorphisms fixing its distinguished vertex,
and `H` the first-link automorphisms fixing `q`, both expressed in the
shared-star coordinates. Two embeddings produce the same second link
exactly when they differ by right multiplication by `K`. Thus their number
is `|G|/|K|`. Relabelings preserving the first link and the ordered anchors
act by left multiplication by `H`. The ordered union classes are therefore
the double cosets `H\G/K`.

Burnside's formula counts these orbits under `g -> h*g*k^-1`. A pair `(h,k)`
fixes a map when `h = g*k*g^-1`. There are zero fixed maps unless `h` and `k`
are conjugate in `G`; otherwise the number is their centralizer order. The
implementation computes every needed conjugate over the complete 10,368
maps and sums these exact integer fixed-point counts, dividing by `|H|*|K|`.

An isomorphism of unions preserving the ordered anchors recovers and
preserves the first and second full links by their incident blocks. It
cannot identify distinct first-link classes or distinguished-point orbits.
Within one type pair, it is exactly an `H`/`K` identification as above.
Thus summing the double-coset counts does not silently assume that a
completion has any automorphism. The counts concern the fixed unions only.

# Direct count check and small pilots

`check_double_cosets.py` uses a different counting method. It constructs
explicit left and right actions on all 10,368 group elements and counts
connected components. There are sixteen distinct coordinate stabilizer
subgroups, so 256 action problems cover every one of the 1,156 type pairs.
Every direct count agrees with the Burnside count, totaling 4,578,210.
This checks the counting arithmetic on the supplied groups; a separate
agent is auditing the full normalization and map-completeness argument.

Four pilot unions use one first-link type from each source class and the
next class cyclically as the second source link, with the identity coordinate
map. They are explicit examples, not representatives of the millions of
classes. Both nineteen-block links in every pilot pass both the package
verifier and standalone checker after relabeling to points 1 through 15.
The 33-block unions are also checked twice and correctly reported as partial.

The pilot archive is ignored scratch at
`experiments/scratch/degree19-overlap-five-pilots-v1.0.1`. Each raw model has
4,368 globally lexicographic Boolean block variables and 3,063 linear rows.
It selects the 33 union blocks, forbids every other block through either
anchor, and leaves all `C(14,5)=2,002` avoiding blocks available. It requires
64 blocks in total, complete triple coverage, both anchor degrees 19, every
other degree at least 19, and every pair multiplicity at least five. Thus
31 additional blocks are required. No hint or objective is present. The
same raw rows are saved for a unit-box LP relaxation. No CP or LP solve is
performed; solver seeds and time budgets are intentionally unset.

An initial preparation used the wrong standalone verifier result field
(`covered` rather than `covered_subsets`) and failed before creating any
model. That incomplete v1.0.0 archive is retained with a failure record.
The corrected v1.0.1 preparation passed all link and partial-union checks.
Ruff passed for all enumeration, direct-count, roadmap, and preparation code.

The factorization source hash is
`283162362b895a20b797b2ee97bae45cd4d165af88b3bed2824b04a79151b3e2`;
the factorization archive hash is
`f9a8c81ef8bb7fb7fa113d113be17c446a1efd9ca8bb98b3110272a2d8c20064`.
Neither is changed by the separate pilot preparation or direct count check.
