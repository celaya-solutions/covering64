```text
Document:    Complete Degree Branches for the C(16,5,3) Search
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      36de3e23ee2a893643fb3b96ec2ea7a11804e321d27f7e8fb18b860dca3db231
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Complete degree branches

The 64-block goal is still open. This note explains reductions used to search
for a cover, not an unrestricted nonexistence result. No novelty claim is made
for the elementary arguments or the smaller covering-design classification.
The four-class result was published by J. L. Allston, R. W. Buskens and
R. G. Stanton in 1988: [An examination of the non-isomorphic solutions to a
problem in covering designs on fifteen points](https://combinatorialpress.com/article/jcmcc/Volume%2004/vol-004-paper%2015.pdf),
Journal of Combinatorial Mathematics and Combinatorial Computing 4, 189–206,
Theorem 12 on page 204. The computation here independently reconstructs that
known classification for reproducible use in this search.

## The degree split

In a triple cover on 16 points with five points per block, every pair occurs
in at least five blocks: its 14 possible third points must be covered in
groups of at most three. For a fixed point, its 15 pair incidences therefore
total at least 75, and each incident block supplies four. Every point has
degree at least 19.

If at most 64 blocks exist, either some point has degree 19, or every point
has degree exactly 20 and there are exactly 64 blocks. Indeed, the sum of the
16 degrees is five times the block count, at most 320. Thus both branches
together preserve existence. Degree ordering and incumbent incidence patterns
are not imposed on this split.

## All degree-19 links

Relabel a degree-19 point as 1 and remove it from its 19 incident blocks. The
result is a pair cover of points 2 through 16 by 19 distinct quadruples.
Every point in this link has degree at least five. Its degree sum is 76, so
one point has degree six and the other 14 have degree five.

For each pair, subtract one from its coverage multiplicity. The resulting
excess multigraph has degree four at the degree-six point and degree one at
each other point, because a quadruple supplies three pairs at each of its
points. Consequently it is the simple graph consisting of a four-edge star
and five disjoint edges. Relabel its center as 2, its four leaves as 3 through
6, and the remaining edges as (7,8), (9,10), (11,12), (13,14), and (15,16).

There are six quadruples containing point 2. Regard these six unordered
quadruples as graph vertices. Each star leaf belongs to two of them and gives
one edge of a graph A. There can be no loop or parallel edge in A: a loop
would repeat a point within a quadruple, and parallel edges would repeat a
pair of leaves whose required multiplicity is only one. Thus A is a simple
four-edge graph with maximum degree three.

Each remaining point belongs to exactly one of the six quadruples. Join the
locations of the two points of each matched pair to obtain five edges of a
multigraph B. Loops are allowed and use two slots. At every graph vertex,
the degree in A plus the degree in B is three.

Conversely, any such pair (A,B) specifies six possible hub quadruples, up to
renaming star leaves, matched pairs, pair endpoints and the six quadruples.
Enumerating A under all permutations of its six vertices, then B under the
automorphisms of A, therefore loses no link. There are 1,335 labeled A graphs,
eight A classes and 206 combined hub classes.

For each class, the remaining 13 quadruples avoid point 2. They must exactly
fill the residual pair multiplicities. Every one of the 1,001 quadruples on
points 3 through 16 is considered; a quadruple is ineligible only if it would
use a pair with zero residual demand. Complete residual enumeration gives
114 labeled links: 12, 4, 2 and 96 in hub classes 1, 4, 44 and 47, respectively,
where these are zero-based indices in the saved ordered list. The other 202
hub classes have no link. The standard-library enumeration visits 31,989
nodes and agrees exactly with a separate CP-SAT enumeration.

Explicit checked relabelings place all 114 links in four isomorphism classes,
one per surviving hub class. The corresponding hub automorphism groups have
orders 48, 8, 4 and 384. Exhausting the allowed excess-graph relabelings also
distinguishes the four representatives from one another. The classification
data and independent replay artifacts are under `experiments/2026-10-03/` in
`link-classification`, `link-hub-independent`, and `link-hub-campaign.json.gz`.

After this finite classification is independently replayed, searching all four
fixed representative links is an existence-preserving replacement for the
degree-19 branch. Each extension retains all 3,003 five-point blocks avoiding
point 1; none is removed through an incidence or rotational assumption.
Timeouts on these four searches remain inconclusive.

## Point-essential regular covers

Call a triple private to a block if that block is its only selected covering
block. Consider a regular degree-20 cover of 64 distinct blocks. If a point p
in a block D occurs in no private triple of D, replace p in D by any point y
outside D. Triples of D avoiding p stay in the replacement; triples containing
p are already covered elsewhere. Coverage is preserved and p now has degree
19. If the replacement is already selected, simply delete D, obtaining a
63-block cover with p still at degree 19. If exactly 64 blocks are required,
add any unused block avoiding p; there are 3,003 possible such blocks.

Therefore, together with the degree-19 branch, the regular branch can require
every block-point incidence to belong to a private triple. This restriction
preserves existence across the two branches. It does not assert that every
regular cover has this property.

For each triple T, the model uses a Boolean u(T) equivalent to coverage(T)=1.
For every block D and point p in D it imposes

    sum(u(T) for T contained in D and containing p) >= x(D).

Block variables retain lexicographic order. Any selected block may be renamed
to {1,2,3,4,5}; point degrees, private triples and existence are unchanged.
The encoding is checked against every subfamily of a small complete block
universe. Separate controls test the replacement argument on the known full
65-block cover and the case where replacement produces a duplicate block.

The optional positive-hole-budget mode searches partial covers in this family.
It supplies possible starting states only. It has no completeness claim about
all partial covers, and any zero-hole result still requires both full-cover
verifiers. An unsuccessful run is not a proof against either complete branch.

## Redundant private-triple count bounds

For any collection of M tracked triples, let I count their block incidences,
h their uncovered triples and u their private triples. Each of the other
M-h-u triples has at least two incidences. Therefore

    I >= u + 2(M-h-u), or u + 2h >= 2M-I.

A regular20 family of64 blocks gives (M,I)=(560,640) globally and(105,120)
at each point. For each pair with block multiplicity lambda, (M,I)=(14,3lambda).
Thus the CP model may add u+2h>=480 globally, >=90 at each point, and
u+2h+3lambda>=28 at each pair, using the corresponding indicators each time.
The bounds remain valid for partial covers with exact cardinality and degrees.
For full covers, the native model adds at most80 nonprivate triples globally
and at most15 at each point. These aggregates are consequences of the exact
coverage indicators; they impose no additional structural assumption.
