```text
Document:    Independent Constructive Clebsch Point Link Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      865f3c0ec3e534254919b9acf00658c7fe51b47bb325fb4f7a66debe13aac690
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent affine point-link replay

All four explicit local constructions and all 256 recorded point maps passed. This
is local feasibility, not a complete 64-block cover or proof of global compatibility.
No solver was imported or called. The producer module was not imported.

The checker independently enumerates the affine plane as all translated one-dimensional
subspaces of GF(4)^2, using a multiplication table. It finds 20 distinct lines and checks
that they partition all 120 pairs of the 16 affine points. After deleting the origin,
it verifies the 15 retained lines, five disjoint rays, assigned centers, function-cycle
rules, five extensions, exact coordinate-to-canonical bijections, and lexicographic IDs
among all 1,365 four-subsets of the fifteen remaining labels.

Each canonical witness has 20 distinct four-subsets. All 105 pairs have the intended
multiplicity: 90 at one and 15 at two. The excess has five degree-four vertices and ten
leaves. An independent graph classifier confirms C5, C4 with a leaf, a triangle with a
two-edge path, and a triangle with two leaves at distinct vertices. It checks every
excess triangle and its upper bound of one local block. Each witness covers 80 distinct
outside triples.

All 256 explicit bidirectional maps are bijective and map the precise source excess
graph to the claimed canonical graph. Source profiles are checked directly for induced
Clebsch-path triples and their pair demands. The class census is C5: 16; each other
class: 80. The per-profile census also agrees with the producer.

Across the maps, the checker evaluates 26,880 exact pair rows, 116,480 outside residual
rows, and 143,360 full triple upper bounds. Every mapped local link leaves 440 nonnegative
triple incidences to be supplied by 44 additional blocks. Both package and standalone
cover verifiers run on all 256 lifted partial families, including the four saved examples:
each has 20 blocks, 185 covered triples, 375 holes, and valid=false. All saved witness
bytes, representative hashes, verifier receipts, and producer file hashes agree.

Twenty-two damaged controls are rejected: missing or duplicated blocks/maps, malformed
function and point labels, forbidden cycles, repeated centers, wrong variable IDs,
excess edges, triangle caps/counts, class names, inverse maps, residual totals/histograms,
and witness/profile hashes. The independent checker and Ruff both pass.

These witnesses establish feasibility of the four proposed local diagnostics, so the
four planned local solver calls are unnecessary. They are one chosen construction per
local shape. They do not enumerate every local decomposition or label isomorphism.
Excluding a later residual completion from a chosen link excludes that branch only.

To replay, use a fresh sibling audit directory with the same checker and frozen inputs;
the checker refuses to overwrite its saved review. The recorded source and input hashes
are listed in review.json and files.json.
