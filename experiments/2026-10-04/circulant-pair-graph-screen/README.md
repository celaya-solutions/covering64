~~~text
Document:    A Non-Clebsch Circulant Pair Graph and Eight Excess Profiles
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      eec13cd6ef24583c9ce33e3a23b6908c54f1587432b16849cc9a23c9a973128c
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
~~~

One graph type survives this finite arithmetic screen. It is the graph on Z16
with steps {+1,-1,+3,-3,8}. Its nonedge common-neighbor histogram is
{1:16,2:48,3:16}, which proves it is not isomorphic to the Clebsch graph, where
every nonedge has two common neighbors. Eight explicit eighty-triple excess
profiles satisfy all required pair and point sums for this new graph. These
are arithmetic profiles, not covers. No optimizer ran and no cover model was
prepared by this arithmetic script.

## Complete screen of the stated 21 graph choices

Every pair 1 <= a < b <= 7 defines a five-regular graph on sixteen vertices
with steps {+a,-a,+b,-b,8}. All twenty-one graphs have forty edges.
Thirteen contain triangles and fall outside the requested triangle-free branch;
this does not prove those pair profiles impossible. Four more are triangle-free
but have a nonedge with no common neighbor. Such a pair cannot receive its
required excess unit from a P3, so these four triangle-free profiles cannot
extend to the stated cover profile.

The four remaining named graphs have (a,b) equal to (1,3),(1,5),(3,7),(5,7).
Multiplication of Z16 by 1,5,3,7 respectively maps the first graph onto each;
the saved explicit point permutations verify every edge. Thus there is exactly
one isomorphism type among the survivors, without a general graph-isomorphism
search.

Every survivor passes the necessary cut bounds. All 11,440 seven-point sides
and 6,435 unordered balanced cuts are enumerated per graph. The maximum seven
cut is 31 and the maximum balanced cut is 32. There are nine tight balanced cuts.
The screen saves all cut histograms and the first maximizers.

## Required excess and tight-cut implications

The proposed pair profile has multiplicity six on graph edges and five on
nonedges. As in the checked triangle-free pair-excess argument, its eighty
triple-excess units must be P3 triples. Every nonedge chooses exactly one common
center, while each graph edge belongs to four chosen paths. These conditions
also give triple-excess degree fifteen at every point.

Sixteen nonedges have a unique common center before any cut deductions. For an
8-versus-8 cut of excess size 32, the total internal triple incidences in a
64-block cover equal exactly 2*binomial(8,3)=112. Every internal triple must
therefore occur exactly once. An excess P3 internal to either side is forbidden.
Across all nine tight cuts this forbids thirty-two of the 160 possible P3s.
It leaves thirty-two nonedges with a forced center and forty-eight with two
centers. The forced paths load thirty-two graph edges twice and eight graph
edges zero times. The remaining binary choices must still satisfy edge demands;
they are not forty-eight freely independent decisions.

## Eight explicit profiles

Use zero-based coordinates only for this formula; every saved point label is
one-based. The five nonedge difference representatives are d=(2,4,5,6,7).
For each d choose a center offset c, and take all translates of {0,d,c}.
There are 3*2*2*1*2=24 translation-invariant choices before checking edge demands
and tight cuts. Exactly eight pass:

~~~text
c = (1, c4, c5, 3, c7)
c4 in {1,3}; c5 in {8,13}; c7 in {8,15}.
~~~

For each of these eight choices, all eighty sorted distinct P3 triples are
saved and recounted. Each graph edge has excess four; each nonedge has excess
one; each point has excess fifteen. All profiles avoid every forbidden internal
P3. The eight are not asserted to be nonisomorphic or to exhaust arbitrary
excess profiles for the graph. Completeness is only for the twenty-four stated
translation-invariant center choices.

All 128 point links are checked. Their five degree-four vertices are the graph
neighbors of the deleted point. The other ten vertices have degree one and are
pendant leaves attached to this core. The profile-level core census is two C5,
four C4-with-leaf, and two triangles with leaves at distinct triangle vertices.
Every point in one profile has the same type. These are link excess graphs;
the script does not choose or fix any twenty-block link construction.

## History, scope, and controls

A targeted search of the saved reports, scripts and October 3-4 experiment
metadata found no previous model for this circulant pair profile. The earlier
regular-action exhaustions and cyclic-orbit searches constrained the cover
itself to symmetry orbits. A symmetric pair or excess profile does not imply
that the cover is invariant. A future exact-profile model must therefore retain
all 4,368 lexicographic pentad variables unless a further reduction is proved.
This history check makes no claim about lost artifacts or all prior literature.

Six damaged-profile controls are rejected: a missing triple, duplicate triple,
invalid label, Boolean label, non-P3 triple, and a changed valid P3 with wrong
pair demands. The script uses only the Python standard library. Ruff passes.

~~~sh
uv run python experiments/2026-10-04/circulant-pair-graph-screen/build.py
~~~

The summary SHA256 is
27dd7ebf038525fa55b9c6ac631127b20ffbf6f424c4c20b4d784a93c1737d03.
The profiles SHA256 is
dec757aef695e80546c0408a5ebe116cb4666e9472e1e3b429d07bef2990a908.
