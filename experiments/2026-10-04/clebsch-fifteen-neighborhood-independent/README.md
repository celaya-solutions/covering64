~~~text
Document:    Independent Fifteen Neighborhood Forcing Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      5732910cf030d6bd3a9bc0ba05432ce437b16d04a3eab465362b1cc823939f1b
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
~~~

The fifteen-to-sixteen forcing proof passes independent checking. Combined with
a fresh replay of the separately checked sixteen-neighborhood contradiction,
it proves that any cover with the Clebsch pair profile contains at most fourteen
Clebsch neighbor pentads. This does not exclude all Clebsch-profile covers or
give an unrestricted lower bound for C(16,5,3).

## Independent enumeration

The audit reconstructs the graph from a four-cube and antipodal edges, transported
to the saved labels. It fixes the fifteen neighborhoods other than N(1). Their
150 distinct triples are exactly the independent triples outside N(1); the ten
triples inside N(1) remain uncovered. The pair-profile proof already checked in
the sixteen-neighborhood audit requires every independent triple exactly once.
Any new pentad must therefore avoid all 150 covered independent triples.

The audit enumerates all 4,368 pentads and reconstructs exactly 258 admissible
ones. It compares every saved block, lexicographic ID, graph degree sequence,
type, independent-triple count, point-one membership, and point-one graph degree.
Connectedness is checked for every non-independent type.

| Type | Count | Point-one graph degree |
| --- | ---: | --- |
| C5 | 192 | 2 in 60 blocks; absent in 132 |
| C4 with leaf | 30 | 3 in every block |
| P5 | 30 | Point one absent |
| Star K1,4 | 5 | 4 in every block |
| Missing neighborhood | 1 | Point one absent |

## Exact forcing identities

Let a,b,c,d,e count these five types in the table's order. Let x count selected
C5 blocks containing point one. The audit verifies every candidate's
contribution to all five identities. It derives the right-hand sides from the
fifteen fixed blocks and pair multiplicities six on graph edges, five elsewhere:

~~~text
a + b + c + d + e = 49
5a + 5b + 4c + 4d = 240
b + c + 4d + 10e = 10
x + b + d = 15
2x + 3b + 4d = 30
~~~

The point-one pair sum is 80, so it occurs in twenty pentads. Five fixed
neighborhoods contain it, leaving fifteen occurrences. Its five graph-edge
pairs require thirty incidences. These facts give the last two rows.

The checker performs exact integer row arithmetic to obtain:

~~~text
b + 2d = 0
c + d + 5e = 5
b + 3d + 5e = 5
~~~

All counts are nonnegative. The first equality forces b=d=0. The third then
forces e=1, so the missing neighborhood is selected. The remaining equations
give c=0, a=48, x=15. Thus the unique aggregate solution is
(a,b,c,d,e,x)=(48,0,0,0,1,15). This is exact arithmetic, not a numerical relaxation
or a search through candidate covers.

## Every choice of fifteen neighborhoods

All sixteen explicit XOR translations are independently reconstructed. Each
sends its stated omitted point to point one and is checked to preserve graph
edges, map that point's neighborhood to N(1), and map the other fifteen
neighborhoods onto the fixed set. Graph preservation also preserves pair and
triple types. Thus the argument applies to any chosen fifteen neighborhoods.

The prior certificate, independent checker, and independent audit are bound by
their exact hashes. The audit freshly replays the prior checker in memory:
all 431 supplied force steps, nine failed-positive-literal contradictions, and
192 symmetry maps pass again. It does not rewrite those frozen files. A cover
containing at least fifteen neighborhoods would therefore contain all sixteen,
contradicting that separately checked finite proof.

## Controls and replay

Nineteen damaged inputs are rejected. They alter candidate completeness,
labels, IDs, types, rooted degrees, independent-triple counts, Boolean versus
integer fields, identity rows and bounds, the count solution, normalization
maps, prior proof pins, the prior audit result, and scope. All six producer
file hashes match. The checker and imported prior checker use only the Python
standard library. There are zero optimizer calls and zero cover searches.
Ruff passes.

~~~sh
uv run python experiments/2026-10-04/clebsch-fifteen-neighborhood-independent/check.py
~~~

The independent audit SHA256 is
bd811ed04a34265113bffa75fff4a00461bdec12c58dd21bdd83be83a64a8929.
The producer summary SHA256 is
2cb7a539e586c3c35c926bcc8ac1888ebf8e003fe8b1f783e42ba8bcab50ab8f.
