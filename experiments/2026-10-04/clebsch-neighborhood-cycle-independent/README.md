~~~text
Document:    Independent Clebsch Neighborhood Cycle Gate
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      94c2f55a31e4840bac46c106936657bcdfd4b2fe609ad747869ae1d74411de2f
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
~~~

The frozen model passes this independent gate. This checks only the construction
with the sixteen Clebsch neighbor pentads and forty-eight induced cycle pentads.
It is not an unrestricted reduction for C(16,5,3), or a reduction that follows
from fixing the neighbor pentads alone. No optimizer ran during this audit.

## Independent finite checks

The checker starts from the four-dimensional cube with antipodal edges and
transports its labels to the saved model. The producer instead starts from the
sixteen even five-bit words with distance-four adjacency. Every pair agrees.
The graph has forty edges, degree five, no triangles, and two common neighbors
for every nonedge.

All 560 triples split into 160 independent triples, 240 triples with one edge,
and 160 induced paths P3. The sixteen neighbor pentads cover every independent
triple exactly once and contain none of the other triples. There are 192 induced
five-cycles. Every one-edge triple has four cycle carriers; every P3 has six.
Each cycle contains five triples of each of these two kinds.

The checker enumerates all 4,368 pentads and confirms that exactly the 192 cycles
contain no independent triple. It independently builds and compares every
variable and constraint in the saved protobuf, including otherwise unexpected
fields. There are 16 fixed-one, 192 binary, and 4,160 fixed-zero variables in
lexicographic order. The 561 rows have 48,048 coefficients: one cardinality row
and all 560 triple rows, each with its full 78-column support. There is no hint,
objective, omitted triple row, or hidden enforced constraint.

## Why the restricted recipe is valid

Assume a complete cover has pair count six on Clebsch edges and five on its
nonedges. The earlier pair-excess proof implies that every non-P3 triple occurs
once and every P3 occurs once or twice. In particular, every independent triple
occurs once. If the cover also contains all sixteen neighbor pentads, those
pentads already use every independent triple. Each remaining pentad therefore
contains no independent triple and must be one of the 192 cycles. There must be
forty-eight such cycles. This is completeness within both stated assumptions.

Conversely, a selection satisfying the saved rows has the required pair counts.
For any graph edge, there are six one-edge triples containing that edge. Each
selected cycle through it contributes once to this sum, so exactly six cycles
contain it. Neighbor pentads contribute zero. For any nonedge, there are also
six one-edge triples containing it. Each selected cycle through it contributes
twice, so exactly three cycles contain it; two neighbor pentads bring its pair
count to five. These coefficient identities are checked for every pair and
every cycle, not inferred from a sample selection.

The triple rows ensure coverage. The pair counts imply point degree twenty and
sixty-four total blocks. They also imply the P3 upper bound two by the earlier
pair-excess proof. Explicitly retaining cardinality and the upper bounds does
not discard a cover within this recipe. The model does not choose a particular
set of eighty doubled P3 triples or a tournament recipe.

## Controls and launch boundary

Twenty altered models are rejected. They damage each of the three domain
classes, a variable name, a missing variable, cardinality, a missing or extra
row, enforcement, objective, hint, and the bound, support, or coefficient for
each of the three triple kinds. Fresh fake-process checks exercise normal exit,
termination after 35 seconds, kill after a further 5 seconds, and duplicate
launch rejection. The fake processes do not sleep or invoke an optimizer; a
patched solver entry point raises if called during these controls.

The gate binds all six manifest pins, the producer source and the saved
parameters: one call, one worker, seed 2026106201, a 30-second native budget, a
35-second watchdog, and 5-second termination grace. The root agent owns the
actual launch. The source writes a candidate only after a feasible response and
then requires the package verifier and standalone checker before labeling it a
complete64 result. A later runtime audit must verify any actual result.

An UNKNOWN result remains inconclusive. An INFEASIBLE response would be a solver
report for this recipe, not an independently checked proof or a global lower
bound.

## Earlier work

The independent research report records two broader Clebsch probes: a free
excess-choice model with the fixed pair profile, and a model using the seed-zero
excess profile. Both returned UNKNOWN. The continued research report later
records feasible numerical fractional solutions for sixteen representative
tournament excess recipes. Those relaxations did not produce integer covers or
exclude a profile. A separate constructive point-link audit proves local link
feasibility for those recipes, without global compatibility.

A targeted search of the saved scripts, reports and October 3-4 experiment
metadata found no earlier solve of this sixteen-neighborhood/192-cycle recipe.
That search is a history check of this workspace, not a claim about all prior
literature or missing historical artifacts.

The checker passes Ruff. Replay with:

~~~sh
uv run python experiments/2026-10-04/clebsch-neighborhood-cycle-independent/check.py
~~~

The gate SHA256 is
3b3eb88b04923e69b31404dcc4fe942e09c41936cd7fc88502a7015284f05891.
The checker SHA256 is
8b608c8373d75d5ccb1de08b62540d6f44343f6d97d1ebcd89280b9a04837e61.
