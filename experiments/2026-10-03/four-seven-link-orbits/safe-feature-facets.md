```
Document:    Exact Feature Hull Cuts for the Four-Sevenfold Branch
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      2b155c9af481f271210ae59352ac88dee51f3b2cb651cf9147e6edbc264445e5
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Exact feature hulls, kept separate from the first five cuts

The 102 cycle and 56 matching representatives surviving the first complete
LP screen give 43 and 33 distinct feature vectors. Their exact four-dimensional
convex hulls have 18 and 23 facets. Six cycle facets and twelve matching facets
exclude at least one of the previously certified impossible link types.
These include the first five rules and thirteen additional families.

No model or existing cut helper was changed by this analysis. The new families
would provide sixteen additional cycle rows and thirty-six additional matching
rows after transport to all four heavy groups. Independent review is recorded
separately from this derivation.

## Coordinates and exact enumeration

The coordinates are `(H,S,A,C)` in this order:

- H: hub–hub edges in the seven-edge first-heavy link.
- S: anchor–hub edges whose endpoints belong to the same group.
- A: anchor–hub edges between adjacent groups of the hub-excess graph.
- C: anchor–anchor edges between adjacent groups of that graph.

Adjacency means positive hub-pair excess: a cycle edge or a doubled matching
edge. There are five hub endpoint incidences in a first-heavy link. Hence the
remaining anchor–hub count is `B=5-2H-S-A`, while the remaining anchor–anchor
count is `D=2+H-C`. Both identities hold for every integer link.

`derive_feature_facets.py` uses only the Python standard library. It first finds
five affinely independent surviving vectors, certified by a nonzero integer
4-by-4 determinant. It then exhausts every four-vector subset: 123,410 in the
cycle case and 40,920 in the matching case. Nonzero 3-by-3 cofactors supply a
primitive integer normal to each candidate hyperplane. The script retains a
hyperplane exactly when every surviving vector lies on the same side. This
checks 10,957 and 3,957 distinct hyperplanes, respectively.

Each retained hyperplane contains four affinely independent vectors. It is
therefore a facet of the full-dimensional hull. Conversely, every facet has
four affinely independent vertices, so the enumeration is complete. All
normals, bounds, equality points, and dimensional witnesses are saved. No
floating hull solver or rational approximation is used.

## Additional cycle inequalities

Each row means `normal dot (H,S,A,C) <= bound`. The last column counts original
representative types violating that row; each has a separately checked positive
LP exclusion certificate. Counts overlap.

| Normal | Bound | Violating orbit types |
| --- | ---: | ---: |
| (-2,0,1,1) | 4 | 12 |
| (0,-1,0,-1) | -1 | 4 |
| (1,0,1,-1) | 2 | 6 |
| (2,0,1,-1) | 3 | 6 |

For example, the first two are `A+C<=4+2H` and `S+C>=1`. Together with the
existing `A<=3` and `H-C<=0` rules, these six facet families exclude 20 of the
27 originally excluded cycle orbit types. They do not recover every exclusion.

## Additional matching inequalities

| Normal | Bound | Violating orbit types |
| --- | ---: | ---: |
| (-4,-2,1,0) | -2 | 32 |
| (-3,-1,1,1) | 1 | 15 |
| (-2,-1,1,-1) | -1 | 22 |
| (-1,-1,1,-2) | -1 | 27 |
| (0,0,1,-1) | 1 | 13 |
| (1,-1,1,-2) | 1 | 12 |
| (1,0,1,-1) | 2 | 5 |
| (1,0,1,0) | 3 | 4 |
| (3,1,3,1) | 11 | 8 |

The first is `A+2<=4H+2S`. Including the existing `H+S>=1`, `A<=2`, and `C<=2`
rules, these twelve facet families exclude 46 of the 73 originally excluded
matching orbit types. Shared feature vectors can still have different LP
outcomes, so a hull in these four coordinates cannot encode every exclusion.

## Why the cuts are valid for covers

An integer cover in the regular four-sevenfold branch supplies one of the
completely classified first links. It cannot use an orbit with a checked
infeasibility certificate, so its feature vector belongs to the finite set of
surviving vectors and hence to their convex hull. Every facet inequality is
therefore valid for that integer cover. The derivation independently checks
that each violating original representative has a positive exact certificate
gap in the final audit; it also verifies the audit's complete-screen hash.

The feature vector is directly recomputed from every representative's edges
and from all 59,940 explicit orbit members. It is invariant under the permitted
relabelings. Both weighted hub graphs are vertex-transitive with eight group
automorphisms. For every selected facet and target heavy group, the script
checks the forward and inverse transport of all 69 allowed outside-edge
coefficients. This includes zero and negative coefficients, not just support.
The explicit permutations and signed global lexicographic variable indices are
saved in `target_groups` for each selected facet.

Transporting a hypothetical cover by a graph automorphism is a label change;
it imposes no invariance requirement on the cover itself. Fractional points of
the original LP can violate these integer-valid hull cuts. Their removal is
not an inconsistency with the previously checked fractional witnesses.

## Evidence and reproducibility

The implementation handoff is `safe-feature-facets.json`. It contains all hull
facets; only entries with nonzero `excludes_certified_orbits` have transported
rows. The `already_in_five_rules` flag distinguishes the thirteen new families.
Each row uses `normal dot features <= upper_bound`. Its block-variable
coefficient is the dot product of that normal with the edge's four class
indicators. Point labels are one-based; groups and the 4,368 block-variable
indices are zero-based. The full lexicographic variable order is preserved.

The JSON records hashes of its source, complete feature table, orbit archive,
full-screen result, and final independent certificate audit. Reproduce with:

```sh
uv run python experiments/2026-10-03/four-seven-link-orbits/derive_feature_facets.py
```

Artifact SHA256:
`7f79089fd414539551863b367b161ee1b8a5dffbaf1e5bd9013ee6ac33cc3e51`.
The header hash covers the body after the header fence, including its initial
blank line.
