```text
Document:    Independent Five Overlap Factorization Review
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      90d8fad6734ed7101c8b9e80703a66a6e1d4a7f6ba73ec6c59eb1fae31cbe697
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent result

The frozen factorization passes an independent audit. There are 34 target
anchor types and 34 source distinguished-point types, giving 1,156 pairs.
The shared five-triple star has 10,368 automorphisms. Across all type pairs,
there are 11,985,408 compatible coordinate maps, 7,402,752 distinct pinned
second links, and 4,578,210 classes of ordered anchored unions. Reversing the
two anchors has not been quotiented.

`check.py` independently enumerates star maps by permuting the five triples
and rejecting changes in their intersection pattern. The 12 possible triple
permutations and every compatible internal bijection produce all 10,368 maps.
The saved map list matches exactly. Coordinates, full links, all 34 point
orbits and both stabilizers are reconstructed using the separately recomputed
full automorphism groups from `../degree19-roadmap-independent`.

For each of the 19 stabilizer elements, the checker explicitly counts every
solution of `g*h*g^-1=k` over all 10,368 maps. It uses these solution counts
directly in all 1,156 Burnside sums. It does not infer these counts from the
saved conjugacy signatures. Every centralizer, numerator, denominator and
per-pair class count agrees. All four explicit unions regenerate exactly as
33 distinct blocks with nineteen blocks at each anchor and exactly five shared
blocks. Eight damaged-factorization controls are rejected.

# Why the factorization is complete

A fivefold pair link is five triples on fourteen remaining points. Every point
must occur at least once, so fifteen total incidences leave exactly one point
occurring twice. Hence two triples meet at that point and the other three
triples are disjoint from each other and from those two, except for their
stated single intersection. This is exactly the canonical star. Its group
has order `(2!*2!^2)*(3!*3!^3)=10,368`.

Fix a first degree-19 point link A and its second anchor q in one of the 34
fivefold-neighbor orbits. For a second degree-19 point link, choose one of the
four classified unpointed link types and then the source vertex that maps to
the first anchor. Its degree in that link must be five. The 34 source point
orbits exhaust these choices. Coordinate charts identify the source and target
five-triple stars with the canonical star, so every compatible labeling is
represented by exactly one element g of its full automorphism group G.

Two coordinate maps yield the same pinned second link exactly when they differ
by right multiplication by K, the source full-link automorphisms fixing its
distinguished vertex. The right action is free, so there are `|G|/|K|` pinned
second links. A relabeling preserving the first link and its selected second
anchor belongs to H, the corresponding target stabilizer. Thus ordered unions
for this pair of pointed-link types are exactly the double cosets `H\G/K`.
The first and second links can be recovered from the union as all blocks
through their respective tagged anchors, so no further identifications are
hidden by taking their union.

Burnside's lemma for the action `(h,k): g -> h*g*k^-1` counts fixed maps by
`g*k*g^-1=h`. The checker counts the inverse-conjugation equations; replacing g by its
inverse gives the same fixed-map count. It divides the sum by `|H|*|K|`. This uses relabeling equivalence, never invariance of an
individual cover. Pointed link types in different full-automorphism orbits
remain separate; reversing the tagged anchor order remains separate as well.

# Scope and replay

This is a complete factorized enumeration conditional on the separately
audited four-class degree-19 link classification. It is not an extension
search, a list of 64-block covers, or a lower-bound certificate. Materializing
millions of unions is unnecessary because every map and its exact regeneration
recipe are preserved in the frozen artifact.

Input SHA256:
`f9a8c81ef8bb7fb7fa113d113be17c446a1efd9ca8bb98b3110272a2d8c20064`.
Run `uv run python experiments/2026-10-03/degree19-overlap-five-independent/check.py`.
The checker calls no optimizer. `audit.json` records its source hash, the
prerequisite audit hash, checked counts and damaged-control results.

# Prepared pilot encoding audit

`check_pilots.py` independently constructs the complete raw protobuf for each
of the four saved explicit unions. It calls neither the model builder nor a
solver. Every one of the 4,368 Boolean variables is in global lexicographic
order; exactly 33 block variables are fixed to one, all 2,002 blocks avoiding
both anchors remain available, and all other blocks are fixed to zero. The
3,063 rows include the exact-64 count, all 560 triple coverage rows, sixteen
point-degree rows (both anchors exactly 19), and all 120 pair lower bounds.
The exported LP rows also match this separate reconstruction exactly.

All four models and 32 damaged-model controls pass in `pilot-audit.json`.
The frozen archive is `../../scratch/degree19-overlap-five-pilots-v1.0.1`.
This is encoding clearance for four conditional pilots. It does not screen
the 4,578,210 factorized classes or constitute a solver result.
