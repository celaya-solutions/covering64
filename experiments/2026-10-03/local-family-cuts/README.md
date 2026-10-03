```
Document:    Safe Local Family Pair and Triple Cuts
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      6cf16d4e1bd0f97cf78f582dff92e63c87432cd94ce87fd47c2bfa2d510f3d47
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

Each local family has 13 quadruples on 13 points, with each point in four quadruples. It covers every pair outside the graph consisting of a two-edge spoke and five disjoint edges. At most one spoke edge may be missing, so the missing-pair graph is a matching.

At a point, the four quadruples give 12 pair incidences. There are 12 other points. Therefore the number of repeated-pair incidences equals the number of missing pairs at that point, which is at most one.

Two bounds follow:

- A pair appears in at most two local quadruples. Three appearances would give both endpoints at least two repeated-pair incidences.
- A triple appears in at most one local quadruple. Two appearances would repeat two different pairs at each of its points.

The proof uses only local degree and local coverage. It does not require global full coverage, point-essentiality, an outside-pair lower bound, or an opposite-spoke omission in a different family. Point relabeling preserves the proof. Thus the cuts remain valid for the explicit relaxed partial mode.

The helper `scripts/local_family_cuts.py` checks both bounds directly on all 88 independently enumerated local families. Before adding cuts to a saved model, it verifies the lexicographic Boolean block variables and the rows that imply local degree four, required pair coverage, and at most one missing spoke. It refuses a model missing those assumptions. It adds 156 pair bounds and 572 anchored-triple packing bounds for anchors 2 and 3, preserving all other fields and avoiding duplicate cuts.

Focused controls check the classified families, malformed families, an unjustified model, variable ordering, idempotency, and compatibility with the relaxed 14-hole candidate. The 120-second full-cover pilot fixes representative `r4-000`; its result concerns only that fixed-family model. A solver timeout is inconclusive, and a solver negative alone is not a separately checked proof.

The pilot finished with `UNKNOWN` after 120.007648 seconds, using seed 2026102400 and two workers (OR-Tools 9.15.6755). No candidate was returned. The durable `pilot-metadata.json`, `pilot-result.json`, `pilot-source.py`, and `pilot-manifest.json` preserve the command, source revision, exact source, solver version, and artifact hashes. The model and solver log remain in ignored scratch. This timeout yields no infeasibility conclusion.
