```
Document:    Independent Core-Avoiding Pool Gate
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      feb70abe92ac31f09d05043c3813c2cde18e119bcd3a670f5982f1b56c54829f
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Core-avoiding pool delta gate

Both models exactly match the earlier independently reconstructed pool formulation, with exactly two extra rows. Each extra row sums the 60 global block variables for one independently transported known core and limits that sum to 59. The two point maps were independently applied to the saved core and checked against the respective three-hole source states.

The ten source states, pools of 277 and 337 blocks, 60 random additions, support histograms, solver seeds, two 30-second limits and four-worker setting are unchanged. The complete hint now equals the regular five-hole seed. Every hinted block and hole Boolean was checked; the hint satisfies every row and overlaps the two cores in 0 and 59 blocks.

The complete protobuf comparison checks all 4,928 variable names/domains, 1,124 rows, all coefficients/domains/enforcement literals, the objective and every hint value. Eight damaged controls cover weakened or corrupted core rows, incorrect hints, and changed original cardinality or coverage rows. No optimizer ran during this gate.

This is a construction experiment with two explicitly declared restrictions, not a complete reduction of the covering problem. Avoiding these two specific labeled cores does not prove absence of another relabeled 60-block core.

## Completed response replay

Both cases returned FEASIBLE with five holes and numerical bound zero. The callback saved the regular five-hole hint; both final responses were distinct equal-objective states. Every saved and final state was independently recounted and passed both verifiers. Every final response bit was checked against the full frozen model, including both core restrictions.

Both final states have degree histogram 19:3,20:10,21:3. The elite final state overlaps the two declared cores in 1 and 59 blocks and has triple histogram 0:5,1:494,2:55,3:1,6:2,7:3. The expanded final state overlaps them in 0 and 59 blocks and has triple histogram 0:5,1:494,2:56,6:1,7:4. No better hole count was found. No new isomorphism search was run, so the absence of every possible relabeled core is not asserted.

`postcheck.json` preserves all saved-state and final-response profiles, verifier receipts, raw hashes and four rejected damaged-response controls. This bounded pilot does not establish either restricted optimum or an unrestricted lower bound.
