```
Document:    Audited Pair-Five Hint Inventory
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      992341dabe6d83ff04a60be530862915df5e9d1ebc666e8ec1499d7a42a8e8e5
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Audited pair-five hint inventory

The best state in this bounded inventory has six uncovered triples. It contains
64 distinct blocks, every pair appears at least five times, its three audited
core overlaps are [2, 2, 0], and its maximum global five-heavy partition weight
is 22. Both the package and standalone covering verifiers freshly confirmed its
six holes and canonical hash. This is a legal near-cover hint, not a cover.

The selected file is
`experiments/2026-10-03/reduced-family-heuristic/penalty-2026100363/search-control_before-1-h6.txt`,
SHA256 `797dada195b23eecc808798eb12c8e4e7ccd7edd026fbdf22dea5b341f9ea2de`.
It is identical to that campaign's initial state and the earlier audited
`trades-2026100362/search-diverse-30-h6.txt`. The documented v1.3 twenty-hole
qualified state also passed these three filters, but was not the best eligible
state in the declared inventory.

## Declared coverage

The script reads eight named native metric-audit folders and five named recent
independent postchecks. It checks 202 candidate paths, representing 134 distinct
states. Of those, 26 paths representing 17 states pass the pair floor, all three
core caps, and the global partition condition. Selection orders eligible paths
by holes, original-core overlap, then path. The inventory does not claim to scan
every saved file in the repository.

Every candidate file must match a saved audit hash and parse as 64 distinct,
ascending five-element blocks on labels 1 through 16. The script rejects four
malformed controls: a missing block, duplicate block, repeated label, and label
outside the universe. It does not invoke an optimizer.

The selected state's pair histogram is 88 pairs at five, 24 at six, and eight at
seven. Every point has degree 20. Its only heavy triples are {1,2,3} at seven,
{4,7,12} at six, {5,8,11} at seven, and {10,14,15} at six. These facts describe
the hint; no point-degree, incidence, family, or symmetry constraint is proposed.
Passing the declared filters is not a claim that all other necessary conditions
or historical qualification scores pass.

## Exact maximum and pair necessity

A triple of multiplicity at least six has weight five, plus one if multiplicity
is at least seven; all other triples have weight zero. The independent inventory
maximizes weight over every disjoint subset of positive-weight triples. Any such
subset has at most five members and extends to five disjoint triples on sixteen
points, leaving one point out. A maximum-weight subset cannot gain positive
weight on extension. Thus this exact packing maximum equals the maximum weight
of every five-triple partition. A value at most 26 excludes every global
five-heavy obstruction used by the frozen DP model.

In a full cover, fix any pair. There are fourteen triples containing that pair.
Each selected five-block containing the pair covers exactly three of those
triples. Therefore every pair must occur at least ceiling(14/3) = 5 times.
This argument applies to every full cover, without any regularity assumption.
It can reject near-covers while preserving every valid 64-block cover.

## Provenance

`result.json` binds all thirteen input audit receipts, every screened candidate,
the three-core manifest, both fresh verifier receipts, and the checker source.
The selected candidate's historical v1.2.1 native source, runner, and auditor were
resolved to preserved scratch snapshots matching the old recorded hashes.
Its binary, campaign metadata, seed, and family inputs also match their saved
hashes. Current v1.3 sources were not substituted for these historical versions.
`files.json` indexes this report, source, result, and the two verifier receipts.

Preliminary lint and historical-source-binding attempts were preserved under
ignored `experiments/scratch/pair-five-hint-inventory-development-20261004/`.
No source artifact, old audit, old candidate, or optimizer output was replaced.
