~~~text
Document:    Independent Finite Clebsch Cycle Certificate Check
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      14c03978b6654c83da89c44b0b52cee8950f9836a5d8790befd952250e3c34b3
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
~~~

The finite certificate passes independent replay. It proves there is no cover
with both the Clebsch pair profile and all sixteen Clebsch neighbor pentads.
Equivalently, the sixteen-neighborhood plus forty-eight-cycle recipe is
impossible. It does not exclude every cover with a Clebsch pair profile, and it
does not prove a global lower bound for C(16,5,3).

## Conditional reduction

The pair profile has multiplicity six on the forty graph edges and five on the
eighty nonedges. Each point then occurs twenty times and there are sixty-four
blocks. For a complete cover put h(T) = multiplicity(T) minus one. The total
excess is eighty. Its sum on triples containing a pair is four for a graph edge
and one for a nonedge. Thus the total graph-edge incidence in the excess is
160. The graph is triangle-free, so each excess unit contributes at most two
edges. Equality forces every positive excess onto a P3 triple. Its unique
nonedge has total excess one, so each P3 multiplicity is one or two. Every other
triple has multiplicity one.

The sixteen neighbor pentads cover each independent triple once. Fixing all of
them therefore forbids any other pentad containing an independent triple. The
checker enumerates all 4,368 pentads and finds exactly 192 remaining candidates:
the induced five-cycles. It independently rebuilds the graph from a four-cube
with antipodal edges, instead of the producer's even five-bit representation.

The reduced matrix contains all 400 non-independent triples in lexicographic
order: 240 exact-one rows and 160 rows bounded from one to two. The final row
requires forty-eight selected cycles. All 401 rows, all 192 cycle blocks, and
their original lexicographic variable IDs match the certificate.

## Trace replay

The certificate initially selects cycle zero. Each saved propagation step cites
one row and assigns all of that row's unknown variables. A step assigning zero
must already have as many selected variables as the upper bound. A step
assigning one must need all remaining unknown variables to reach the lower
bound. The checker verifies the cited row, exact unknown set, Boolean value,
bound condition, and absence of a prior contradiction in that cited row.

For each failed positive literal, the checker copies the current base state,
selects that literal, replays its supplied force steps, and checks the claimed
contradiction directly. The literal is therefore zero in every solution of the
base state. The checker then replays the saved base steps. It never generates
search branches or repeats the producer's propagation algorithm.

All nine failed literals, in order, are:

~~~text
4, 5, 20, 12, 13, 18, 19, 6, 14
~~~

There are 431 checked force steps across the initial state, nine hypothetical
branches, and the base traces. Every saved branch endpoint matches the replay.
The final base state has 24 selected and 95 rejected cycle variables. Reduced
row 379 represents triple (9,11,16). Its support is cycles 96,104,168,177, whose
values are respectively 1,0,0,1. The row requires exactly one, giving the final
contradiction.

## Exhausting the recipe by explicit symmetry

The certificate supplies 192 point permutations, one taking reference cycle
zero to each cycle. Each is checked as a bijection on labels 1 through 16.
The checker directly verifies preservation of graph edges, the complete fixed
neighbor set, the complete cycle set, and every triple-row type and bound. The
incidence supports follow from the same point bijection; the cardinality row is
also preserved. The accompanying five-coordinate permutation and even-word XOR
description must produce exactly the supplied point permutation.

Every recipe solution would select forty-eight cycles, so it would select at
least one. Applying the inverse of its verified map would give a recipe
solution selecting reference cycle zero. The checked contradiction excludes
that possibility. No assertion about an unverified automorphism group or a
single representative orbit is needed.

## Independence and controls

This checker uses only the Python standard library. It imports neither the
producer nor OR-Tools. It does no optimization, no cover search, and no branch
generation. The graph, domain and matrix are reconstructed; only the proposed
logical steps and explicit permutations come from the certificate.

All 27 damaged controls are rejected. They alter matrix bounds and support,
cardinality, domains, initial assumptions, forced assignments, branch traces,
branch conflicts and endpoints, the final contradiction, automorphism count,
targets and maps, coordinate metadata, and scope. Ruff passes.

Replay with:

~~~sh
uv run python experiments/2026-10-04/clebsch-neighborhood-cycle-certificate-independent/check.py
~~~

Certificate SHA256:
6802e49098940c70253dbf17e0a44bc05acb800185d85356dc5031faa6c545fc.
Independent audit SHA256:
de03e575af4237a99f5ad10083ac7f0651021c8349d3250162cef2972f752e84.
