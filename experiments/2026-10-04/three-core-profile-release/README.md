```text
Document:    Three-Core Three-Profile Release Pilots Outcome
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      be894600ed9f786bfba4460d45ae2675560e84a142c42b260f075a0332affce7
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Result

Both cases ran exactly once after the independent gate. The adaptive case ended
with 12 uncovered triples; the full-universe case ended with 10. Neither found a
cover. Both statuses were FEASIBLE and both objective bounds were zero.

| Case | Wall seconds | Starting holes | Final holes | Original-core overlap | Composite |
| --- | ---: | ---: | ---: | ---: | ---: |
| adaptive-952 | 120.01267079205718 | 13 | 12 | 1 | 781 |
| full-4368 | 120.0080802909797 | 10 | 10 | 1 | 651 |

The adaptive callback saved objectives 846 and 781. Its native final response
matches the last saved family. The full callback saved objective 651 only;
its native final response is a different tied family, sharing 62 blocks with
the saved hint. All witnesses and native responses were preserved.

The independent postcheck passed all five saved/final records, representing four
distinct families, through both the package verifier and standalone checker.
The exhaustive global five-heavy scan found no forbidden profile in any of
those records. The final three named core overlaps are `1,7,50` for the adaptive
case and `1,7,55` for the full case.

The postcheck also checked complete native response assignments and rejected
seven damaged-response controls plus malformed-label, duplicate-block and
damaged-cardinality witness controls. Its relabeled-core screen found one
necessary deficit partition per state and no cap-55 violation among 242 explicit
core images. This screen remains inconclusive about all point relabelings;
a necessary partition alone is not an explicit transported-core violation.
No optimizer calls were made by the independent check.

# Frozen design

These are two bounded release pilots with different legal hints. They are not a
controlled comparison of pool size. The goal is to find a 64-block cover while
retaining all checked cuts. Two optimizer calls completed under the frozen budget.

Both pilots retain the earlier pools: 952 blocks for the adaptive case and all
4,368 lexicographically ordered blocks for the full case. The earlier two
core-at-most-55 rows and two five-heavy profile rows remain. One independently
checked translated core row and its newly observed profile partition are added.
Each model now has 4,958 Boolean variables and 1,188 linear rows.

The added core comes from the exact transport in
`../third-core-independent/audit.json` (SHA256
`6a3881254e8c659459174bb79630c2b78d946d35f40f52ca472149410820deb9`).
Its point images are `[16,15,12,5,11,8,4,7,3,6,1,2,10,14,13,9]`.
The audit checked all 16 labels, 4,368 blocks, 560 triples and 43,680 incidences
and transported the already checked upper bound of 55 retained core blocks.
The profile partition is
`(1,2,3), (5,6,7), (8,12,16), (9,10,11), (13,14,15)`.
It uses the same proved five-heavy rule as the two earlier partitions.

# Hint selection

`hint-selection.json` deterministically recounts all 15 saved/final paths in the
independent strong-core postcheck. Seven pass all three core bounds and all three
profile rules; four of those paths also lie entirely in the adaptive pool.
For each pool, eligible paths are ordered by hole count, original-core overlap,
then path. This produces:

| Case | Hint | Holes | Three core overlaps | Composite |
| --- | --- | ---: | --- | ---: |
| adaptive-952 | strong adaptive `best-01-h13-c1.txt` | 13 | 1, 7, 51 | 846 |
| full-4368 | strong full `best-03-h10-c1.txt` | 10 | 1, 8, 55 | 651 |

The full hint contains three blocks outside the frozen adaptive pool: zero-based
lexicographic variable IDs 1151, 1278 and 2299. Those are variable IDs, not point
labels; point labels remain 1-based. The pool is unchanged, so the adaptive
pilot uses its own best legal hint. The hints therefore differ by design.
Eligibility here means compliance with the declared cuts, not certification
against every possible relabeled core.

# Budget and freeze

Both pilots use seed 2026104103, four workers, and a 120-second solver budget.
The objective remains `65 * holes + original_core_overlap`. Every selected slot
is released; no radius or extra overlap cap is added. All block variables retain
lexicographic ordering, and the hint assigns every model variable.

The runner, manifest, checked source paths, proof references, hint paths, model
protos and shared parameter proto are hash-bound. Raw files are under
`experiments/scratch/three-core-profile-release-20261004/`; they stay out of Git.
Source SHA256:
`7c0fc47ad481e8a80631bea85855aa2648c53b0608a21fc9d9fbb58ed6cbf6ee`.
Manifest SHA256:
`546c44b04b7eded3aaac2d0a3a7c0450612f07530f2edbd85284d8c33479292d`.
The runner passed Ruff before freezing. The independent exact gate passed before either call and reconstructed all
4,958 variables and 1,188 rows, checked every complete hint bit, and rejected six
damaged models. The two cases each ran once; no further solve was made.

Gate SHA256:
`ceb77c7914702a4500874698a8c0c9687d3baf9059bd43064e44f6e1ecd26343`.
Result SHA256:
`da1af94782bd4c01af231967c4e8da396cd51e2e13e4f1f4fce835cd67419c90`.

Independent postcheck SHA256:
`276a359ca09fac44bf93b456fcd3773b2786732755e2e60af4f01e553b889193`.
It is stored in `../three-core-profile-release-independent/postcheck.json`.

# Interpretation

All saved and final candidates passed both verifier recounts, which correctly
identify them as partial covers. UNKNOWN and
timeouts are inconclusive, and CP-SAT infeasibility alone is not an independently
checked theorem. These bounded pilots cannot establish global nonexistence.
