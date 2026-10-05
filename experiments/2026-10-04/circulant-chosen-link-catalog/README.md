```
Document:    A Constructive Catalog for the Circulant Pair Graph
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      fa435815bb4ded629207cdc77729facc7264ce776f6b3898d22c4d0193eafd76
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

The constructive next route is to vary the chosen point-link embedding and
the excess profile together before making any global completion call. The
previous one-map-per-link approach unnecessarily pinned an arbitrary local
embedding. This catalog provides 5536 distinct twenty-block partials and
195296 compatible (profile, partial) pairs, all at point 1, without an
optimizer or a residual support screen.

## Inputs, census, and exact scope

The pair graph has steps plus/minus 1, plus/minus 3, and 8 on Z16, translated
to labels 1..16. Reconstruct all 1300 supplied excess profiles from the saved
48-bit center-choice masks, forced paths, and geometry. Check every profile
has eighty distinct triples and pair codegrees four on graph edges and one
on nonedges. Their 20800 point links have the four previously constructed
core types: 8512 triangle-path2, 6272 C4-leaf, 4768 C5, and 1248
triangle-two-leaves.

At point 1 there are only 38 different excess graphs. Each belongs to 28 to
40 of the supplied profiles. For each class, enumerate all permutations of
its five degree-four vertices preserving core edges, then every permutation
of degree-one leaves onto the leaves of the mapped heavy vertex. Degrees
distinguish heavy vertices from leaves, so this enumerates the full excess
graph automorphism group. Apply each automorphism to the one chosen canonical
twenty-K4 witness, then map it to each actual point-one excess graph.

| Class | Distinct point-one excess graphs | Images per chosen witness | Distinct partials |
| --- | --- | --- | --- |
| C4-leaf | 12 | 96 | 1152 |
| triangle-path2 | 16 | 96 | 1536 |
| triangle-two-leaves | 2 | 144 | 288 |
| C5 | 8 | 320 | 2560 |

Each chosen witness has trivial stabilizer within its excess graph
automorphism group: all enumerated images are distinct. Global block-ID
deduplication also confirms 5536 distinct actual partials. Every partial
passes all 105 local exact pair equations and has eighty distinct outside
triples. Its twenty lifted pentads therefore cover 185 distinct global
triples, leaving 375 holes.

This catalog is complete only for all excess-graph isomorphism images of
the FOUR specific saved canonical twenty-K4 witnesses. It is not a catalog
of all affine constructions, all point-link decompositions, or all covers.
The supplied profile list has its separate enumeration audit. Translation
of the circulant graph sends any selected point to point 1 and preserves the
profile constraints; retaining all supplied profiles avoids assuming cover
invariance. Nothing here requires the block family itself to be cyclic.

## Workload and proposed staged check

The 195296 compatible pairs each have 3003 possible remaining pentads and
455 outside-point residual triple rows. A single residual support pass has
at most 88859680 row support popcounts and 15623680 zero-row mask unions.
A check of conflicts among immediately forced blocks adds at most another
88859680 row popcounts; it is not iterative propagation. Cardinality adds
one cheap support check per pair. Every exclusion must save an explicit
insufficient-support or forced-conflict certificate. Survivors are merely
candidates for further work and are not feasible completions.

Freeze a screen manifest before running a deterministic 1000-pair benchmark
with a ten-second wall budget. Use its measured cost to choose the full
finite pass budget. Keep complete counters and a saved cursor if the cap
is reached. Do not launch a global optimizer or iterative propagation as
part of this stage.

## Files

Run `uv run python experiments/2026-10-04/circulant-chosen-link-catalog/build.py`
to regenerate the catalog. `canonical-images.json` stores all 656 canonical
automorphism images and their maps; `link-fibers.json` maps the 38 actual
excess graphs to their classes, label maps, profile lists, and partial-ID
ranges. `partial-catalog.json` stores all 5536 partials as twenty global
zero-based lexicographic five-block IDs, with canonical text hashes.
`profiles.json` saves reconstructed profiles and their original choice masks.
The summary and file index pin inputs, source revision, all counts, and scope.
