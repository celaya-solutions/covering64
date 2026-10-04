```text
Document:    Eight Plus Eight Extension Construction
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      23a4c24b5659367dbb9142862193430f43b565c21624a89a8c4bdfbefae9163b
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Two groups of eight: extension recipe

This is a restricted construction search. It does not claim that every 64-block cover has this shape. The points split into {1,...,8} and {9,...,16}. On each half use the affine Steiner quadruple system on the binary three-cube: each nonzero normal vector gives two complementary four-point planes. Keep the planes in four normal directions, producing eight quadruples of point degree four. Those quadruples cover 32 internal triples exactly once, leaving 24 other internal triples.

Type A omits directions {1,2,3}; type B omits {1,2,4}, with integers encoding three binary coordinates and the usual binary dot product. The three explicitly tested recipes are AA, AB and BB. No completeness claim about all covering designs, all mixed recipes, or all quadruple systems is needed for these trials.

Extend each quadruple by one point from the other half, and each of the 24 leftover triples by two points from the other half. Choosing one extension of every base gives 32 blocks per half, hence 64 distinct five-blocks. The available extensions number 8*8+24*28=736 per half, or 1,472 total. The four intersection sizes distinguish the groups across halves, and an extension has a unique base, so the 64 choice groups are disjoint. All 112 internal triples are covered exactly once. The remaining 448 triples cross the partition and must each be covered at least once.

Each saved model retains all 4,368 block variables in lexicographic order, fixing the 2,896 ineligible blocks to zero. It has 625 rows: exact cardinality 64, 64 one-extension equations and 560 covering rows. The internal covering rows and cardinality are redundant but make inspection simpler. There are no hints, objective, fixed final point degrees, core caps or orbit constraints. Regularity of the selected quadruples does not impose regularity of the final family.

The bounded campaign has three sequential 120-second, four-worker calls with seeds 2026105401 through 2026105403. Each has a 145-second watchdog and five-second termination grace. A first observed feasible candidate stops native search, then every saved assignment is checked against every model domain and row and reconstructed for both independent covering verifiers. The campaign stops on a verified cover or an incomplete/failed child. There are no retries or transferred budgets. A timeout is inconclusive, and CP-SAT INFEASIBLE is not an independently checked proof.

The runner reuses the frozen typed vector checker, canonical block ordering, two verifier invocations and atomic callback recorder from the checked two-point-star v2 experiment. Here there are exactly 4,368 variables; its callback's empty hole-variable tail intentionally causes first-feasible stopping. Model and group files, parameters, logs, responses and source/version hashes are retained in ignored scratch. Root owns the sole launch after an independent gate binds the manifest.
