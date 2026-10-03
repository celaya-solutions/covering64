```
Document:    Independent double-hub enumeration audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      3d4c4f09b7d06358b4572208833e75f301cfe188a55a74d8c70da6379af76c44
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent double-hub enumeration audit

The recorded enumeration is complete for its stated branch, conditional on the complete four-class classification of optimal C(15,4,2) links. No defect was found. This audit does not import or call the enumerator or its classification helper.

## Exact scope and completeness argument

Consider two distinct points p and q of a full cover, each with degree 19, whose pair occurs in six blocks. In the optimal 19-block link of p, q is the unique point with replication six. The same argument makes p the unique replication-six point in q's link. Relabel p as 1, q as 2, and the first link as one of the four classified representatives. The six common blocks then fix all six hub-containing blocks of the second link.

Each of the second link's 15 points appears in its six hub blocks. Any admissible point relabeling therefore induces a bipartite incidence-graph isomorphism between the source's six hub blocks and the prescribed target blocks. Conversely every such isomorphism gives a bijective point map that preserves those six blocks. Exhausting graph isomorphisms thus enumerates every possible relabeled second link. It permits every arrangement of singly occurring points and does not impose the first link's excess matching on the second.

The audit uses NetworkX 3.7 to enumerate these incidence-graph isomorphisms, independently of the source's row-permutation/grouping method. For each first link it separately enumerates automorphisms of the complete 19-block incidence graph, extends them to fix point 1, and constructs the orbits of all 32-block unions. These transformations preserve the entire first link and point 2. One representative per orbit preserves existence within this branch.

This covers only r(p)=r(q)=19 with pair incidence six. It does not cover a lone degree-19 point, degree-19 pairs sharing five blocks, or the regular degree-20 branch. The 270 representatives are orbits under the specified first-link automorphisms, not a claimed classification of all unmarked 32-block designs. Anchor reversal or other additional equivalences may identify further duplicates.

## Results

| First link class | Distinct second links | Second excess matchings | First-link automorphism order | Union orbits |
| --- | ---: | ---: | ---: | ---: |
| 1 | 216 | 42 | 4 | 68 |
| 4 | 216 | 42 | 2 | 126 |
| 44 | 48 | 24 | 2 | 28 |
| 47 | 96 | 1 | 4 | 48 |
| Total | 576 | — | — | 270 |

Every saved source map was checked as a bijection and applied directly. Every recorded canonicalizing map belongs to the independently enumerated first-link automorphism group and maps its union to the saved representative. All candidate block IDs retain lexicographic ordering. Fresh direct pair, point and triple counts verify all 576 links and all 270 partial unions; the saved package/standalone hashes and statuses agree. Each union has 32 distinct blocks, both anchor degrees 19, and six common blocks. Its `valid:false` status is expected because it is a partial seed.

All nine damaged controls are rejected: omitted second link, duplicated second-link row, damaged source map, incomplete automorphism group, damaged block ID, incorrect orbit assignment, malformed block, repeated block within a link, and artificially fixed second matching. `result.json` records the rejection reasons, exact orbit-size histograms, source/template/archive hashes and NetworkX version. Ruff passes for the checker.

The audited candidate archive SHA256 is `bfca95755b84ead2d98e21cfe2abfae4bb4b549e520b89bb9d8a83ed442d137d`. Original artifacts and source snapshots remain under `experiments/scratch/double-hub-links-20261003/`. This audit proves no extension is feasible or infeasible and establishes no global lower bound.

Run from the worktree root:

```sh
uv run --with networkx==3.7 python experiments/2026-10-03/double-hub-audit/check.py
```
