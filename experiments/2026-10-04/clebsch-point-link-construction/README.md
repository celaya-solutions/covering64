```
Document:    Four Constructive Clebsch Point Links
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      62da86f295dfcf94a3a6f53cc69ad84669f8f5d2ffc0dca99af02edd73774e45
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

Every point link in the sixteen audited tournament excess profiles admits an
explicit twenty-block local construction. All 256 label maps pass all 105 exact
pair equations and all 455 outside-point residual checks. This is local
feasibility only. It proves neither a global 64-block cover nor compatibility
between independently chosen point links. The four proposed local CP calls are
canceled; this construction used no optimizer or solver budget.

## Exact local problem and four classes

Fix a profile H and point p. Removing p from its twenty incident pentads must
give twenty distinct four-subsets on the other fifteen points. Their pair
multiplicity must be 1 plus the indicator of membership in E_p, where
E_p consists of the pairs ab with pab in H. Each E_p has fifteen edges, five
vertices of degree four, and ten vertices of degree one. The five heavy
vertices are the Clebsch neighbors of p. Their induced core has five edges;
the other vertices are pendant leaves.

For the regular-tournament recipe, a direction has two wins. Its auxiliary
cycle orientation chooses exactly one winning square with the edge at p
positive. Orient the corresponding core edge from this direction to the
other direction. This gives outdegree one; indegree is at most two because
there are two losing directions. There are no loops or directed two-cycles.
Each component contains a directed cycle of length at least three, so five
vertices allow only one component. The core is connected and unicyclic, with
maximum degree three. A cycle of length five gives C5; length four gives
C4 with a leaf. Length three leaves either a two-edge path or two leaves
at distinct triangle vertices. Two leaves at one triangle vertex would give
degree four and is excluded. These are the four classes.

Canonicalization tries all 120 heavy-vertex orders and picks the smallest
lexicographic core edge list, then the smallest original-label order in a tie.
It maps those heavy vertices to 1..5 and maps leaves to 6..15 grouped by their
canonical heavy neighbor, sorting original labels inside a group. The class
counts over all 256 cases are C5: 16; each other class: 80.

## Affine-plane derivation

Use GF(4) represented by binary polynomials modulo x^2+x+1; addition is XOR.
The exact multiplication routine is saved in `build.py`. Points are pairs
(x,y) in {0,1,2,3} squared. Remove (0,0), then label the other points 1..15
in lexicographic point order. Enumerate lines y=mx+b with m then b increasing,
followed by vertical lines x=b with b increasing.

Retain the fifteen lines avoiding the origin. The five origin lines become
disjoint three-point rays L_0,...,L_4 in that line order. Choose distinct centers
c_i from ray L_f(i), taking the smallest unused label in the assigned ray.
Replace each origin line by the four-subset L_i union {c_i}.

| Class | f(0),...,f(4) | Centers in original AG labels |
| --- | --- | --- |
| C5 | 1,2,3,4,0 | 5,6,7,1,4 |
| C4-leaf | 1,2,3,0,0 | 5,6,7,4,8 |
| triangle-path2 | 1,2,0,0,3 | 5,6,4,8,7 |
| triangle-two-leaves | 1,2,0,0,1 | 5,6,4,8,10 |

All maps have no fixed point or two-cycle and indegree at most two. Thus the
distinct-center choice is possible. The fifteen retained affine lines and
five ray triples partition all pairs. Extending a ray adds a three-edge star.
No added edge repeats: a repeated edge would join two centers whose function
images form a two-cycle. Each center has three edges from its own added star
and one from its ray's extension, hence degree four; each noncenter has
degree one. The core is the underlying graph of f. This gives exactly the
desired K15+E pair multiplicities using twenty distinct blocks.

## Triangle caps and global residuals

If an outside triple appeared in two local blocks, all three of its pairs
would be doubled. It would therefore be a triangle in E_p. The two triangle
classes have exactly one such triangle. Its vertices are neighbors of p and
are independent in the Clebsch graph, whereas recipe excess triples induce
paths of length two. Thus that triangle has global demand one and must be
covered locally at most once.

The core triangle is a directed three-cycle whose centers lie on three
different rays. An extended ray cannot contain all three centers; at most
one retained affine line can contain them. The required cap therefore holds.
The saved witnesses each cover their core triangle exactly once. Every
other triple is already forced by its pair demands to have local count at
most one. All 455 remaining triple demands are nonnegative in every mapping.

## Files and replay

Run `uv run python experiments/2026-10-04/clebsch-point-link-construction/build.py`
from the repository root. It uses only finite arithmetic and the two existing
cover verifiers. It writes:

- `classes.json`: original AG coordinates, rays, centers, retained and extended
  lines, the AG-to-canonical bijection, explicit canonical blocks, excess edges,
  caps, and zero-based lexicographic four-block variable IDs (out of 1365).
- `recipe-point-maps.json`: each profile seed and removed point, both label-map
  directions, source-profile canonical hash, cap, residual histogram, and
  hash of the resulting actual-label twenty-pentad partial.
- Four `*-canonical-k4.txt` witnesses and four `*-actual-partial.txt` examples.
  Actual representatives are identified in `summary.json`.
- Package and standalone verifier receipts for each actual partial. Both
  verifiers report twenty blocks, 185 covered triples, and 375 holes. Their
  `valid: false` result is expected: these are partials, not full covers.
- `summary.json`: source revision, input and verifier hashes, class census,
  representative pins, and scope. `files.json` pins this frozen evidence.

To materialize any mapped partial, map each canonical block through the
one-based `canonical_to_actual` array (array entry c-1 gives label c's image),
adjoin the saved point, and sort. Its canonical text hash must match the saved
partial hash. Subtract these blocks' triple multiplicities from 1+1_H. There
are 3003 possible remaining pentads avoiding p, 455 remaining triple rows,
total remaining demand 440, and exactly 44 remaining blocks required. These
are directly reproducible inputs for a future conditional completion, not a
complete enumeration of possible local links or a safe unrestricted reduction.
