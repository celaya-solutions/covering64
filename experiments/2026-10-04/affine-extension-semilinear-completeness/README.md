~~~text
Document:    Completeness of the Four-Class Affine Extension Recipe
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      0a1d42d4ae2149ad58535a1424755fd51dfea82888a9cd24f891826c95de0d64
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
~~~

# Result and exact scope

The 675 fixed-function settings are complete, up to point relabeling, for the
following recipe with one of the four saved excess-core types:

1. Use the saved AG(2,4), delete its origin, and retain its fifteen lines that
   avoid the origin.
2. Extend each of its five three-point origin rays to a quadruple by choosing
   one point outside that ray. Choose five distinct extension points.
3. Require pair multiplicities one or two and require the degree-four core of
   the pair-excess graph to be C5, C4 with a leaf, a triangle with a length-two
   pendant path, or a triangle with leaves at two distinct vertices.

Every such family is equivalent to one of the settings saved in
`../affine-extension-point-variants/settings.json`. Combined with the separate
audit of those settings, its 161 representatives and all their excess-graph
automorphism images are a complete catalog for this recipe at a fixed canonical
excess graph. They give 5,184 distinct families for each of the four classes.

This does not classify every affine construction, every twenty-K4 local
decomposition, or every C(16,5,3) cover. The recipe fixes its retained affine
lines. No cover search, optimizer, or theorem about the global minimum is part
of this certificate. No 64-block cover was found here.

# Why the ray-target function describes the excess core

Write R_i for ray i and c_i for its extension point. There is a unique ray
R_f(i) containing c_i. A loop f(i)=i would leave only three points in the
extended block, so it is excluded.

The fifteen retained lines cover each pair on different rays once and each
pair on the same ray zero times. Extending all five rays supplies each same-ray
pair once and adds the three pairs {c_i,v}, v in R_i. Because the centers are
distinct, an added pair can occur twice only as {c_i,c_j} with f(i)=j and
f(j)=i. Such a directed two-cycle would give that pair multiplicity three.
Thus the required pair multiplicities exclude exactly the directed two-cycles.

With neither loops nor directed two-cycles, the fifteen added pairs form the
excess graph E. Every center has degree four: three pairs from its own extension
and one from the extension of its containing ray. Each of the other ten points
has degree one. The induced graph on the five centers has the five edges
{c_i,c_f(i)}. The undirected core is therefore exactly the undirected graph of f.

Every component of a finite function graph contains a directed cycle. Here every
cycle has length at least three, so five vertices allow only one component and
one cycle. Its undirected graph is connected and unicyclic. On five vertices the
possibilities are the four stated cores and a fifth: a triangle with both leaves
at the same vertex. The fifth is outside the stated scope.

The retained lines have disjoint triples. Two extended rays meet in at most one
point when there is no directed two-cycle; a retained line meets an extended ray
in at most two points. Thus all twenty quadruples are distinct and their eighty
triples are distinct. The fixed-setting audit separately checks these properties.

# Explicit field and semilinear symmetry

Use GF(4)=GF(2)[a]/(a^2+a+1), encoded by 0, 1, 2=a, 3=a+1. Addition is bitwise
XOR. Nonzero points (x,y) in lexicographic order receive labels 1 through 15.
The five ray directions, in the saved order, are
(1,0), (1,1), (1,a), (1,a+1), (0,1).

For every invertible two-by-two matrix A over this field and epsilon in {0,1},
use the point map v -> A(v^(2^epsilon)). There are 180 invertible matrices,
360 distinct semilinear point maps, and exactly 120 induced ray permutations.
Each ray permutation has three scalar lifts. The explicit certificate contains
all matrices, Frobenius choices, point permutations, and ray permutations.
Every map is checked to preserve the complete set of fifteen retained lines.

Consequently the induced projective semilinear action is the full symmetric
group on the five rays. This conclusion follows from the explicit finite maps,
not just from a named-group identification. Ordinary linear maps alone induce
60 ray permutations; Frobenius supplies the other coset. For example,
(x,y) -> (x^2,x^2+y^2) swaps the first two rays and fixes the other three.

# Complete finite function classification

The checker visits every one of the 5^5=3,125 functions on five ray labels.
It excludes 2,101 functions with a loop and then 580 with a directed two-cycle.
The remaining 444 functions split as follows under simultaneous relabeling of
domain and range:

| Core | Fixed function, zero-based | Functions |
|---|---|---:|
| C5 | [1,2,3,4,0] | 24 |
| C4 with a leaf | [1,2,3,0,0] | 120 |
| Triangle with a length-two path | [1,2,0,0,3] | 120 |
| Triangle with leaves at distinct vertices | [1,2,0,0,1] | 120 |
| Triangle with leaves at the same vertex, outside scope | [1,2,0,0,0] | 60 |

For each of the 444 functions, `function-conjugacies.json` saves its exact
conjugating ray permutation and an index of a semilinear map realizing that
permutation. In particular, all 384 functions in scope reduce to the four fixed
functions, with no additional orientation class omitted.

Let p be the saved ray permutation sending f to its fixed representative f0,
so p(f(i))=f0(p(i)). Its semilinear lift sends R_i to R_p(i), c_i to a point in
R_p(f(i)), and the set of retained lines to itself. Reindexing by p transforms
the arbitrary valid center choice to one of the fixed function's distinct-center
choices. A bijection preserves distinct centers. Each target ray has exactly
three points, so the fixed-function enumeration of its five three-point domains
contains the transformed choice.

This proves the stated completeness reduction without enumerating arbitrary
center choices again. The separate setting audit remains responsible for the
675-setting-to-161-representative reduction.

# Passing from recipe equivalence to a fixed excess graph

The construction uses an isomorphism from each setting's E graph to its saved
canonical E graph. Any other isomorphism to the same canonical graph differs by
an automorphism of that graph. Therefore applying the complete Aut(E) group to
every saved representative recovers every labeled family in this recipe with
that canonical E. Relabeling a represented affine plane preserves the recipe,
so the image families also remain within its isomorphism closure.

The checker independently reconstructs the complete Aut(E): degree forces the
five centers and ten leaves, every automorphism permutes the core while
preserving core edges, and the leaves at each center can be permuted freely.
Enumerating exactly these choices gives the same complete automorphism lists
as the frozen catalog. It then forms all family images, checks that different
representatives have disjoint orbits, and records exact stabilizers and union
hashes.

| Core | Aut(E) size | Representative orbits | Orbit sizes | Distinct families |
|---|---:|---:|---|---:|
| C5 | 320 | 17 | 16 of size 320; one of size 64 | 5,184 |
| C4 with a leaf | 96 | 54 | all size 96 | 5,184 |
| Triangle with a length-two path | 96 | 54 | all size 96 | 5,184 |
| Triangle with leaves at distinct vertices | 144 | 36 | all size 144 | 5,184 |
| Total | | 161 | | 20,736 |

The exceptional C5 family has a stabilizer of order five. All other stabilizers
are trivial. Every original chosen-witness image is checked to lie in the new
union. Quadruple IDs use zero-based lexicographic order on four-subsets of the
1-based point labels 1 through 15.

# Point-one workload in the supplied circulant profiles

The 38 actual point-one E fibers partition the 1,300 saved profiles. Each saved
map from canonical E to actual E is a point bijection and is checked against
both edge lists. Thus it preserves the 5,184-family count. Families from
different fibers cannot coincide, because a family's pair multiplicities
uniquely determine its E graph.

| Core | Actual E fibers | Profiles | Distinct links | Compatible profile/link pairs |
|---|---:|---:|---:|---:|
| C5 | 8 | 298 | 41,472 | 1,544,832 |
| C4 with a leaf | 12 | 392 | 62,208 | 2,032,128 |
| Triangle with a length-two path | 16 | 532 | 82,944 | 2,757,888 |
| Triangle with leaves at distinct vertices | 2 | 78 | 10,368 | 404,352 |
| Total | 38 | 1,300 | 196,992 | 6,739,200 |

These are 191,456 additional links and 6,543,904 additional pairs beyond the
previous chosen-witness catalog. A one-pass scan using the previous 455 residual
rows and 80 outside triples has upper bounds of 3,066,336,000 support-row popcounts
and 539,136,000 zero-row union operations. These are workload counts, not timing
estimates or permission to launch a screen. The expanded actual catalog is not
materialized here.

# Evidence and replay

`check.py` completed in 0.534 seconds with Python 3.13.15 at source revision
`2e2ff3b4c75bfe65c3845f5e771a4ec9262f1272`. It records all input/output hashes and
its own source hash in `summary.json`. The enumeration is deterministic and has
no random seed or solver. Its mathematical domain is finite: 512 matrix/exponent
settings, 3,125 functions, and the 161 supplied representative orbits.

`replay.py` uses a literal GF(4) multiplication table and does not import
`check.py`. In 0.255 seconds it replayed every saved map, function conjugacy, and
canonical image union. Its six damaged controls were all rejected: a damaged
point permutation, missing semilinear map, wrong conjugating lift, missing
function, false orbit size, and missing union image. `replay.json` records that
receipt. Ruff passed for both source files.

The complete canonical image unions are in the ignored file
`experiments/scratch/affine-extension-semilinear-completeness-v1.0.0/canonical-image-unions.json.gz`.
Its compressed SHA256 is
`aeceea27fc3bf819c97f8f9334887608a6b49eba2a1bc23c836330e1758d3174`.
The compact canonical uncompressed SHA256 is
`6bf3f84b7d9d8c0f48308d411c9c039a57ee8cac3c7c977eeedb0e754c92d150`.
The tracked orbit certificates preserve the orbit sizes, stabilizers, and
per-orbit union hashes. Existing evidence is frozen; the programs reject
overwriting their receipts.
