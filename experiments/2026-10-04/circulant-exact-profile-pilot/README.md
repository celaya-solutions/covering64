~~~text
Document:    Eight Unfixed Circulant Exact Profile Pilots
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      755b27ad53d192787d378c9037a04a1f03e4f584bdc925ac321f0e156471d9af
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
~~~

Eight exact-profile models are prepared for the non-Clebsch circulant graph on
Z16 with steps {+1,-1,+3,-3,8}. Preparation made zero optimizer calls. The root
agent alone may launch the batch after an independent GO bound to the frozen
manifest. Each model tests one explicitly saved eighty-triple excess profile;
this is not an unrestricted model for C(16,5,3).

## Full block domain and exact rows

Every model retains all 4,368 binary variables, one for each five-point block
in lexicographic order, with labels 1 through 16. All variables have domain
{0,1}; none is fixed. There is one cardinality row requiring sixty-four blocks
and all 560 triple rows. A triple in the selected excess profile has exact
demand two; every other triple has exact demand one. Each triple row includes
all seventy-eight possible block carriers.

There are no fixed point links, fixed neighborhoods, incumbent restrictions,
block-orbit restrictions, symmetry constraints, hints, objectives, or additional
pair/degree rows. Point-link types are metadata only. Translation invariance
of the excess profile does not impose translation invariance on the cover.

The profile arithmetic implies the desired pair counts: summing triple demands
through a graph edge gives 14+4=18, so its pair multiplicity is six. A nonedge
gives 14+1=15, so its pair multiplicity is five. Their point sums imply degree
twenty. The total triple demand is 640, already implying sixty-four pentads;
the cardinality row is explicitly retained and redundant.

## Profile order and budgets

The eight cases follow lexicographic center-offset order in the pinned
profiles file. They are the choices (1,c4,c5,3,c7), where c4 is 1 or 3,
c5 is 8 or 13, and c7 is 8 or 15. Their profile-level point-link core census is
two C5, four C4-with-leaf, and two triangles with leaves at distinct vertices.

Case indices zero through seven use seeds 2026106401 through 2026106408.
An explicit search of the recorded source, JSON, Markdown, protobuf and log
files, including ignored scratch artifacts, found no earlier use of these
seeds. The search excludes only this new producer directory and does not claim
to recover lost historical records. Its exact command and zero-match receipt
are saved.

The approved batch has eight sequential calls. Each has one worker, a native
limit of thirty seconds, a thirty-five-second process watchdog, and a further
five seconds before kill. The aggregate native limit is 240 seconds. Unused
time is not transferred; calls are not retried. An unexpected process error,
watchdog, missing child receipt, or MODEL_INVALID stops the batch. A launch
marker prevents a second execution. The wrapper writes a result after each
completed call so an interrupted batch retains its completed evidence.

## Results and verification boundary

Each case saves its solver log, response, timings, stdout, stderr and hashes.
If a feasible response is found, the complete 4,368-value vector and a block
witness are saved. The package verifier, separate standalone covering checker,
and an exact triple-profile recount must all pass before complete64 is true.
UNKNOWN and timeouts are inconclusive. INFEASIBLE is only a solver result for
that fixed profile unless a separate finite proof is checked.

The frozen manifest has twenty-seven source and data pins, including all eight
models and parameter files, the arithmetic profiles, and both covering
verifiers. It records the source revision, Python and OR-Tools versions.
Large protobufs and eventual raw logs remain under ignored scratch storage.

Root-only invocation after independent approval:

~~~sh
uv run python experiments/2026-10-04/circulant-exact-profile-pilot/run.py --execute --gate PATH_TO_INDEPENDENT_GATE
~~~

Manifest SHA256:
129002dca2ab140a5be66a8879fd7d97fee41f4203ba186d93ca720b335aa7da.
Producer source SHA256:
68fbd3cd539d9d12589de39bef55ff66605f2d3d9227a86b5ed4773253cae0fc.
Seed-check receipt SHA256:
d3a28ecc1859cf3752564c3370c4904aac03df803f84cdea4154d0c4f3ccb2e4.
