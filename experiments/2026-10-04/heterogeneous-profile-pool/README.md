```text
Document:    Two-Partition Profile-Avoiding Mixed Pool Pilot
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      f739f72bd2603174c8bbeb1f4a7efe994ff993514c32a9afba840a7b20a01aeb
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Two-partition profile-avoiding pool preparation

This prepared pilot keeps the previous 277-block elite pool, 337-block expanded pool, 60 fixed random additions, and two declared 60-block core-avoidance rows. It adds the proved five-heavy obstruction for exactly two labeled partitions. The two declared runs have completed; both returned FEASIBLE with six holes. The independent outcome check is in `../heterogeneous-profile-postcheck/README.md`.

The original partition is `(1,3,6), (2,14,15), (4,8,10), (5,13,16), (9,11,12)`. The mapped partition is `(1,2,3), (5,6,7), (9,10,11), (13,14,15), (4,12,16)`. The canonical proof, independent arithmetic checker and its 27,040-assignment audit are bound by hashes under `experiments/2026-10-03/five-heavy-triples/`. The proof does not assume degree regularity.

For each of the five triples in each partition, two exact Boolean indicators encode count at least six and count at least seven. Both directions are explicit. The only profile inequality is `5*sum(six)+sum(seven)<=26`. If any triple is below six, at most four six-indicators and four seven-indicators are true, giving at most 24. When all five are at least six, the inequality permits at most one seven-indicator. Thus it excludes exactly the named forbidden profile and does not impose an unconditional cap on sevenfold triples.

Each model keeps the first 4,368 lexicographic block variables and next 560 hole variables. Twenty threshold indicators follow, alternating six/seven by triple and partition. The result has 4,948 Boolean variables and 1,166 rows. The objective remains the sum of the 560 exact hole indicators. The complete hint is the independently checked 17-hole raw matching seed; its partition counts are `[1,1,1,1,2]` and `[7,7,7,7,0]`.

The preparation checks all 79 possible local multiplicities from zero through 78 and all 243 three-category patterns for the five triples. Exactly 26 patterns are forbidden and 217 allowed. Four deliberately incorrect rules disagree with this table, including the erroneous unconditional cap on sevenfold triples. Independent full model/hint reconstruction and truth-table replay passed before launch.

The frozen budget is two 60-second CP-SAT runs, four workers each, seeds 2026104091 and 2026104092. Model bytes stay in ignored scratch storage and their hashes are in `manifest.json`. The conditional theorem is used here as a construction restriction on partial states. This preparation claims neither a new global bound nor exhaustive screening of all relabeled partitions.
