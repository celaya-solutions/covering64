```text
Document:    Independent Check of the Chosen Circulant Link Catalog
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      b7521f65e4cc5aea3fa06c1ac7bcb2e906f796b28cbd200faef7a4f1ab5d2f4e
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# A finite catalog check

The independent checker confirms all 5,536 saved twenty-block partials and
their 195,296 pairings with compatible excess profiles. Completeness concerns
all excess-graph isomorphism images of four specific saved canonical witnesses.
It does not concern every affine construction or every local decomposition.

For each canonical excess graph, the checker independently exhausts all 120
permutations of its five degree-four centers, then every bijection between
the pendant leaves at corresponding centers. This is complete because degree
distinguishes centers from leaves, and every leaf has exactly one neighbor.
The resulting maps preserve every edge. Their images of the selected witness
give exactly 96 C4-with-leaf, 320 C5, 96 triangle-with-path and 144
triangle-with-distinct-leaves families. All images are distinct, and the saved
maps and families agree exactly with this independent enumeration.

All 1,300 profiles are rebuilt from the separately checked center-choice masks.
The checker reconstructs their 38 point-one excess-graph fibers, verifies the
complete profile partition, checks every map in both directions and transports
every canonical family independently. Each of the 5,536 families has twenty
distinct valid pentads containing point one, covers 185 distinct triples, and
has the required 105 incident triple counts. All eighty outside triples occur
once. Canonical text hashes and global lexicographic IDs also agree.

Five damaged controls are rejected: a missing canonical image, duplicate block,
Boolean block ID, invalid label map and missing excess triple. The checker
imports no producer code, optimizer or covering search. These are direct
structural counts of partial families, not claims that a full cover exists.

The audit SHA256 is
`e832913ef7d0ead42fdcb9c75538654e6dedfdb81091dd44519fa900cfbfe158`.

## Guarded full support pass

The separate launch wrapper verifies the independent gate, full manifest,
all dependencies and the catalog audit before its exclusive launch marker.
The producer has a 45-second cooperative processing budget; the wrapper
adds a 50-second process watchdog, five-second termination grace and kill
fallback. It records the full child-process time, including output hashing.

The sole run completed all 195,296 pairs in 20.226166457985528 seconds without
a watchdog, error or retry. A further independent audit replays every saved
certificate and survivor: 156,846 insufficient-support exclusions, 28,222
forced-conflict exclusions and 10,228 unresolved survivors. The result SHA256 is
`aabd7d06c2a2b297b69086676e12a68ccfd6a532dcf5ea3aeca53d42fde958e3`;
the full replay audit SHA256 is
`d2e5259ab156ff81111742f4c1d8068a436685278bac5fdc9f7a82af34df6137`.
