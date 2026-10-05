~~~text
Document:    Global Model for the Non-Clebsch Circulant Pair Profile
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      4931356e6805105e0f1677ef5da2dcda094eea4e58a69e8395dc82d093e9cc08
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
~~~

One model is prepared for all covers with pair multiplicity six on the edges
of the Z16 graph with steps {+1,-1,+3,-3,8}, and five on its nonedges. The
reduction uses the independently checked complete excess-profile enumeration
and graph automorphisms. It is complete within this named pair profile, not an
unrestricted reduction for C(16,5,3). Preparation made zero optimizer calls.

The table contains fifty-two representatives of excess profiles. These are
not fifty-two cover orbits. The model retains all 4,368 block choices, without
requiring the cover to have any symmetry or fixing any particular point link.

## Why the excess-profile reduction preserves existence

The named pair counts imply twenty occurrences of each point and sixty-four
pentads in total. For a complete cover let h(T) be triple multiplicity minus
one. Its total is eighty, and its sum through each pair is four on graph edges
and one on nonedges. There are 160 graph-edge incidences in h. Since the graph
is triangle-free, an excess unit contributes at most two graph edges, so
equality forces every positive h onto a P3. Each P3 has a unique nonedge with
excess demand one, hence h is zero or one. Each of the eighty nonedges must
therefore choose exactly one common center; each graph edge must occur in four
chosen paths.

The independently checked finite enumeration is complete for these conditions.
Tight-cut identities force thirty-two path choices and leave forty-eight binary
ones. Two different exact methods find the same 1,300 valid profiles. A complete
enumeration of graph automorphisms finds thirty-two maps, with identity and
reflection forming the stabilizer of one point. Their explicit action partitions
the 1,300 profiles into fifty-two orbits, with every member and representative
saved in the independent orbit certificate.

Suppose a cover has any of these 1,300 profiles. The checked orbit action gives
a graph automorphism taking that profile to its chosen representative. Applying
the same point permutation to every pentad preserves distinct blocks, complete
triple coverage, and the named pair profile. Every image pentad is still one of
the 4,368 model variables. Thus some representative-table model solution exists
whenever a cover with the named pair profile exists. Conversely, any model
solution is directly such a cover. No selected block family is required to be
invariant under the map.

## Variables and exact rows

The model has 4,416 Boolean variables. The first 4,368 are the full lexicographic
five-block variables with labels 1 through 16. The final forty-eight are the
center-choice bits in the archived nonedge order. A zero bit selects the first
center, and a one bit selects the second. All variable domains are {0,1}.

There are 562 constraints:

- One cardinality row requires sixty-four selected blocks.
- All 560 triple rows include their complete seventy-eight block carriers.
  Thirty-two forced excess triples have demand two. For each center-choice bit
  z, its first-center triple has row B+z=2 and its second-center triple has row
  B-z=1, where B is the block-carrier sum. This gives ninety-six conditional
  rows. The other 432 triples have demand one.
- One AllowedAssignments table contains all fifty-two representative vectors
  of forty-eight bits, in increasing representative-mask order.

The table's audited profiles already imply every edge excess load and every
point excess degree. There are no added pair or degree equations, no fixed
links, no fixed neighborhoods or blocks, no incumbent, no objective, no hint,
and no cover-invariance constraint. The only symmetry reduction concerns the
choice of excess profile.

## Approved bounded call and evidence

The root agent alone may launch one call after an independent GO bound to the
manifest. The call has a 300-second native limit, four workers, seed 2026106501,
a 310-second process watchdog, and five seconds of termination grace before
kill. There is no retry, relaunch, or budget transfer. A recorded zero-match
seed search covers saved source, JSON, Markdown, protobuf and log files,
including ignored scratch, excluding only this new producer directory. It
does not claim to recover lost historical records.

The manifest binds fifteen sources and data files: the complete-profile
enumeration, independent replay and orbit evidence, allowed table, model,
parameters, seed receipt, source, and both covering verifiers. It records the
source revision and Python/OR-Tools versions. Large raw model and runtime files
are stored in ignored scratch. Four-worker scheduling can vary between runs;
the actual saved response and logs remain the runtime evidence.

Any feasible response saves all block and center values, its representative
mask, and the witness. Both required covering verifiers, an exact triple-profile
recount, and a pair-profile recount must pass before complete64 is true.
UNKNOWN or a timeout is inconclusive. INFEASIBLE is a solver response for this
named pair profile, not an independently checked proof or a global lower bound.

Root-only invocation after independent approval:

~~~sh
uv run python experiments/2026-10-04/circulant-all-profile-global-pilot/run.py --execute --gate PATH_TO_INDEPENDENT_GATE
~~~

Manifest SHA256:
c3a70ac81bc5174807c3ba150e6924d295a3b2730bec8947921f2176bcc67b72.
Source SHA256:
ab89c2a66fa72182b70fa59874f303cfc40dfb9432e2245322116ef7111ec3fb.
Allowed-profile table SHA256:
0ea1d3ae230b7046b978e6ee84fd0420cb96c48436659181346c879ac34ace79.
