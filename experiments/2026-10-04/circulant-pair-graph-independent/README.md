```text
Document:    Independent Circulant Pair Graph Arithmetic Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      c104693232258d92adf733172143cdc0b2ff77eec608078cb8597fc2c2bccdd1
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent circulant arithmetic replay

The graph on Z16 with steps {+1,-1,+3,-3,8} has 40 edges, degree five at every point,
no triangles, and 160 induced three-point paths. Its nonedge common-neighbor counts
are 16 pairs with one center, 48 with two, and 16 with three. This differs from Clebsch,
whose nonadjacent pairs all have two common neighbors.

The audit rebuilds all 21 candidate step graphs, all recorded cut histograms, and all
four supplied multiplication isomorphisms. Thirteen candidates have triangles; four
triangle-free candidates lack a common center for a nonedge. Four labeled graphs survive
and are explicitly isomorphic. Their maximum seven-cut is 31 and balanced eight-cut is
32. All 71,500 recorded cut sides are recounted independently with adjacency bitsets.

These bounds follow from the exact excess pair loads. If a subset has size s and c
crossing graph edges, excess triples have s(16-s)+3c total crossing-pair incidences.
Every crossing excess triple contributes two such incidences and there are 80 excess
triples, so s(16-s)+3c is at most160. For s=8 this gives c<=32; equality requires every
excess triple to cross the cut. For s=7, c<=32 and odd cut parity strengthens it to31.
The nine tight balanced cuts forbid 32 internal paths. The surviving center choices
force 32 excess triples and leave 48 binary nonedge choices before edge balance.
Forty-eight is the number of binary choices, not the number of assignments.

A separate exhaustive enumeration rebuilds all ten translation orbits of induced paths,
each of size16, and checks all252 five-orbit subsets. Exactly eight profiles pass the
pair demands and tight cuts, matching the saved profiles. The supplemental offset audit
replays every one of the producer's24 center-offset choices: eight accepted and sixteen
rejected because they contain tight-cut internal excess. All saved rejection reasons
are checked. This classifies the translation-invariant profiles, not all excess profiles.

Every profile has80 distinct1-based triples, excess pair loads4 on graph edges and1
on nonedges, and point excess degree15. All128 point-link records are replayed. The
profile core census is two C5, four C4-with-leaf, and two triangles with leaves at distinct
vertices; translations give the same core shape at every point of each profile. Six
malformed profile controls are rejected. Both audit scripts pass Ruff. No producer module
or optimizer is imported or called, and no cover is constructed.

The proposed cover models may use these fixed excess profiles while keeping all4,368
block variables available. Translation invariance of an excess profile does not impose
translation invariance on its block family. No fixed local link, earlier neighborhood,
or Clebsch assumption is justified by this arithmetic. Excluding these eight profiles
would not exclude this pair graph with other profiles or unrestricted C(16,5,3).

Review and supplemental offset receipts are frozen independently. Formatting-only initial
audit attempts were preserved unchanged in ignored scratch; the final tracked sources
and receipts are pinned in files.json.
