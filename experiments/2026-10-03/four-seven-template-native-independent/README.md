```text
Document:    Independent Complete-Template Native Search Gate
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      878444f4d6a417a641b15d5048b466dfe49310aea128695c6149064da7b9b065
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent native template gate

The frozen C++ source `9a58b77cb44d561728a63e9d7e835866f4a0dbfd6306608ee4f85009e65361a1` passed a full static review, independent catalog/seed/state checks and a fresh sanitizer build.

Every exported template row was compared exactly with the independently audited 108-exclusion catalogs: 12,042 matching and 25,020 cycle templates per group. The checker independently enumerated all 1,200 ordinary blocks and their 100 full 12-element seed orbits. Each ordinary block contains at most one point from each anchor triple. It reconstructed both seed orbit unions, all four selected heavy links, exact point degrees and initial uncovered triples.

Across the original smoke runs, 84 saved states and 14 operation descriptors passed exact recount/replay. A separate build of the exact frozen source, with warnings as errors plus AddressSanitizer and UndefinedBehaviorSanitizer, produced 39 further checked states. All four move modes and rollback were exercised. Eight fresh malformed seed/catalog controls were rejected. Saved smoke budgets and final hole claims also matched the raw logs.

A heavy template contains seven blocks through its group's three anchors. Its outside degree is two at that group's hub and one at every other outside point. The four templates therefore contribute degree 10 at each anchor and degree 5 at each hub. The 36 ordinary blocks supply degree 10 and 15 respectively, giving 64 distinct blocks of degree 20 at every point. A single complete-template replacement preserves that entire point-degree vector. Ordinary trades preserve their point degrees and the allowed family.

This gate clears only the authorized matching/cycle 300-second, single-thread construction pilots, at most two at once. It proves no move connectivity, no completeness of heuristic exploration and no impossibility result. Seed rotation is used only for initialization. Coverage, not a pair-score assumption, determines success, and any zero-hole state must immediately pass both covering verifiers. The sibling wrapper binds all source, seed and catalog hashes and handles success during startup controls.

`audit.json` and `controls-audit.json` preserve the independent evidence. Raw fresh binary, logs, states and damaged controls remain under the ignored `experiments/scratch/four-seven-template-native-independent` directory.
