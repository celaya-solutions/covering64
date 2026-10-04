```
Document:    GF16 Inversive Plane Pool and Bounded Pilot
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      91d8f2918d84472e9acaa2a93769551c8eda4d84750ea36c1954e8bac04a9ed5
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Checked construction

Use GF(16)=F2[x]/(x^4+x+1), representing field elements by four-bit integers z and labeling finite points z+1. Infinity has label 17. The GF(4) subfield is {0,1,6,7}. The five-point projective subline consists of these four finite points and infinity.

The builder enumerates all 4,080 normalized nonsingular 2x2 matrices over GF(16), acts on that subline by fractional linear maps, and obtains 68 distinct five-point circles. Every one of the 680 triples on 17 points occurs exactly once; each circle has 60 matrix preimages. Deleting infinity leaves 48 five-point circles and 20 four-point affine lines. Each pair of finite points belongs to exactly one line, and a retained circle meets a line in at most two points.

Adding one external finite point to each line in all 12 ways gives 240 further distinct five-blocks, disjoint from the 48 circles. The pool therefore has 288 blocks. All 80 collinear triples have 12 supporting pool blocks, while the 480 noncollinear triples have four. The original plane 68 and a finite 68-block cover formed from all 48 circles plus one extension per line both passed the package and standalone covering verifiers.

Root independently constructed the same objects using the anisotropic GF(4) quadratic form u^2+uv+omega*v^2, embedded with omega=6 and theta=2. Exact lists of all 68 plane blocks, 20 lines, 48 circles, 288 pool blocks and 560 support rows agree between the two constructions. See cross-construction-audit.json and the separate affine-extension-independent construction/model audits.

# Model and bounded result

The exported model has 288 Boolean variables ordered by increasing global lexicographic block IDs and 561 rows: exact cardinality 64 plus all 560 triple-cover inequalities. It adds no symmetry restriction, point-degree profile, or circle/extension count split. Root independently reconstructed all variables and rows and rejected eight damaged models before execution.

The authorized single CP-SAT pilot used OR-Tools 9.15.6755, seed 2026100371, one worker and 60 seconds. It returned **UNKNOWN** at 60.006202 solver seconds, with no candidate, 6,839,079 conflicts and 19,102,941 branches. UNKNOWN is inconclusive. It provides no nonexistence result for this pool or the unrestricted 4,368-block universe.

The complete model, pool, sources, parameters, solver response and log remain in the two raw folders experiments/scratch/inversive-plane-pool-20261003 and experiments/scratch/inversive-plane-pool-pilot-20261003. manifest.json and result.json bind their hashes. check_result.py read back the saved response and parameters without solving and rejected seven damaged result controls. The original pool/model/run are preserved unchanged while the separate 528-block expansion is prepared. Targeted Ruff passed; root owns full repository checks and commit.
