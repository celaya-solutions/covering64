```
Document:    Complete Surviving Heavy-Link Convex Hull LP Design
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      47cd0650e47de185c504c60609e65cbfda7521716ea085bcfa02b7b378c962df
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Complete local template hulls, with no new search restriction

This prototype replaces the possible fractional heavy links by convex
combinations of every surviving labeled integer link. It retains all links
not excluded by the original 100 independently checked LP certificates. The
four heavy groups receive complete transported copies of the catalog; no
single representative, incidence shape, or cover symmetry is imposed.

The source `build.py` constructs sparse matrices only. No solver was called.
The separate `check.py` reads those files back without importing the builder,
reconstructs the complete catalogs from the archived orbit maps and certificate
IDs, and checks every template column against its seven outside edges.

## Exact formulation

Let A_i be one of the four fixed anchor triples, and let L_i be its complete
catalog of surviving labeled outside-pair links. Each template contains seven
edges, with degree two at its own hub and degree one at every other outside
point. The 69 permitted edges exclude the nine pairs internal to the other
three anchor triples. There is one distinct heavy-block variable x_(A_i union e)
for each permitted edge e.

For every template T in L_i, append a continuous weight lambda_(i,T) in [0,1].
Add exactly these equalities for each heavy group:

```text
sum(T in L_i) lambda_(i,T) = 1

x_(A_i union e) - sum(T in L_i containing e) lambda_(i,T) = 0
    for each of the 69 permitted outside edges e
```

The upper bound one on a weight is redundant with nonnegativity and the
simplex equality, but is recorded explicitly to retain the common [0,1] box
convention. The 4,368 block variables retain their global lexicographic order.
The 400 existing double-triple variables also retain their indices. Weights
begin at index 4,768; the index for group i and base template j is
`4768 + i*catalog_size + j`.

There are four simplex rows and 276 marginal rows. Each appended weight occurs
once in a simplex row and in exactly seven marginal rows. The heavy-block
variables of different groups are disjoint, because a five-block cannot contain
two disjoint anchor triples.

## Why this keeps every possible cover

Every integer cover in the regular four-sevenfold branch has a valid integer
link for each heavy triple. Relabel that group to the first group by a weighted
hub-graph automorphism. The complete 29,970-link classification places its
link in one of the 129 audited orbits. It cannot lie in one of the orbits with
an independently checked positive infeasibility certificate. It therefore lies
in the retained complete labeled catalog.

Set its template weight to one and every other weight in that group to zero.
The simplex and all 69 marginal equalities hold. Doing this for all four groups
extends the cover to a feasible point of the new formulation. Thus no valid
cover is lost.

Conversely, the new rows describe precisely the convex hull of each retained
link catalog: each local block vector is a convex combination of its listed
zero/one incidence vectors. If that local block vector is integral, every
positive-weight template must equal it coordinate by coordinate. Since the
catalog is duplicate-free, its representation is then one-hot. No integrality
restriction on the weights is needed to express an integral heavy link.

This is a complete local convexification. It is still an LP relaxation of the
full covering problem; it does not describe the convex hull of all global
covers, and LP feasibility alone does not produce a cover.

## Catalog completeness and transport

The cycle catalog has 25,020 templates: 29,970 minus 4,950 labeled links in its
27 excluded orbits. The matching catalog has 14,202 templates: 29,970 minus
15,768 labeled links in its 73 excluded orbits. The builder uses every explicit
member of each surviving orbit, not only its representative.

Both weighted hub graphs have eight automorphisms and are vertex-transitive.
The builder exhausts those automorphisms and chooses the lexicographically
first one carrying group zero to each target. The point map preserves the
anchor/hub offset within each group. Its inverse is saved.

For each target, the transported catalog is checked for injectivity, the link
degree and edge rules, and inverse-map agreement. The two different group
automorphisms taking zero to that target are also checked to produce exactly
the same catalog. Choosing one of these maps is therefore a naming choice.
Every target keeps the base catalog's template index, with its edges relabeled.

## Exact model sizes

The prototype starts with the frozen, independently audited double-variable
LP base: 4,768 variables, 4,270 rows, and 89,804 sparse coefficients.

| Quantity | Cycle | Matching |
| --- | ---: | ---: |
| Surviving orbits | 102 | 56 |
| Templates per heavy group | 25,020 | 14,202 |
| Appended continuous weights | 100,080 | 56,808 |
| Total variables | 104,848 | 61,576 |
| Appended equality rows | 280 | 280 |
| Total rows | 4,550 | 4,550 |
| Appended sparse coefficients | 800,916 | 454,740 |
| Total sparse coefficients | 890,720 | 544,544 |

The appended coefficient count is `32*catalog_size+276`. If all original
29,970 templates were retained, each case would instead have 124,648 total
variables and 959,316 appended coefficients, with the same row count.

Existing five-rule feature rows and thirteen-family facet rows can be retained
unchanged. That raises the total rows to 4,574 for cycle and 4,598 for matching.
They are logically redundant under the complete surviving-link hull because
they hold for every retained template. The prototype uses the original lifted
base to keep this formulation independent of those optional helpers.

## Saved prototype and readback checks

Large files remain outside Git in
`experiments/scratch/four-seven-template-hull-20261003/`:

- `build.py` and `manifest.json` preserve the generator and input hashes.
- `{case}/base-catalog.json.gz` preserves every labeled template and its source
  orbit ID, in base-link lexicographic order.
- `{case}/extended-rows.json.gz` preserves the base rows, new rows, variable
  width, row descriptions, and catalog transports. Every variable is continuous
  with bounds [0,1] in this LP prototype.

The small tracked `prototype-manifest.json` hashes both catalogs, both sparse
matrices, the generator, source revision, and the complete source/audit inputs.
The final manifest SHA256 is
`21c243c87f44aebe780d8a48e330684d5fcaefbc2a587fa236516d64d8cfc38a`.

`readback-audit.json` checks catalog equality with the exact surviving labeled
set, all 156,888 appended template columns across both cases, all 552 marginal
rows, all eight simplex rows, original-row preservation, and artifact hashes.
It rejects wrong marginal signs, wrong-group lambda indices, and wrong simplex
coefficients in each case. These checks confirm the saved formulation; no LP
feasibility or covering claim is made.

Reproduce into a new ignored output directory, then adjust the readback
checker's SCRATCH path if using a different location:

```sh
uv run python experiments/2026-10-03/four-seven-template-hull/build.py --output experiments/scratch/four-seven-template-hull-replay
uv run python experiments/2026-10-03/four-seven-template-hull/check.py
```

A future bounded LP run must retain these complete columns and save either a
numerical vector with residuals or a separately checked exact exclusion
certificate. Column omission would silently restrict the local template hull.

## Separate exhaustive six-case hub-count split

Another possible refinement is independent of this prototype. Let m_h count
the 36 nonheavy blocks having h hubs, let z count doubled all-hub triples, and
let H_total be the total hub–hub edge count across the four heavy links.

The known totals give:

```text
sum(m_h) = 36
sum(h*m_h) = 60
m3 + 4*m4 = 4 + z
H_total = 10 - m3 - 3*m4 = 6 - z + m4
```

The double-pair demands force z<=2. In the cycle, each all-hub triple consumes
one unit from the two diagonal-pair demands, whose total is two. In the
matching, each consumes two units from the four nonmatched-pair demands, whose
total is four. Other doubled triples use nonnegative amounts of those demands.
Thus z is 0, 1, or 2. Nonnegativity then forces m4 to be 0 or 1.

The six possible integer profiles are exhaustive:

| z | m4 | (m1,m2,m3,m4) | H_total |
| ---: | ---: | --- | ---: |
| 0 | 0 | (16,16,4,0) | 6 |
| 1 | 0 | (17,14,5,0) | 5 |
| 2 | 0 | (18,12,6,0) | 4 |
| 0 | 1 | (14,21,0,1) | 7 |
| 1 | 1 | (15,19,1,1) | 6 |
| 2 | 1 | (16,17,2,1) | 5 |

The separate helper being prepared for this split is
`scripts/four_seven_hub_split.py`. This prototype neither fixes one of the six
profiles nor launches any split solve. Any nonexistence conclusion using a
split must cover all six cases with checked exclusions.

The header hash covers the body after the header fence, including its initial
blank line.
