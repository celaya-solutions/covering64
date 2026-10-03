```
Document:    Corrected Heavy Profile Neighborhood Campaign
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      154f2f182bbe8e97b6d157adcc17ba476e39132dc5cd92534e6f51a2bb93b781
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

No full cover was found. The best candidate satisfying the tested heavy-profile restriction still has six holes.

The original generic repair pilot accepted five-hole and three-hole candidates, but both had a forbidden heavy profile. An initial recount mistakenly used multiplicity at least seven and missed the multiplicity-six triple 4,8,10. The correct condition is five disjoint triples of multiplicity at least six, with at least two of multiplicity at least seven. The earlier statement that the three-hole candidate was eligible is withdrawn. Its coverage count remains correct; it is preserved as a regression control.

The unguarded pilot was stopped after 16 completed solves, totaling 235.242283 solver seconds, and one interrupted solve bounded by 15 seconds. Its frozen sources and partial evidence remain intact. A separate 40-second pilot used the original eligible six-hole seed, two workers, and the explicit conditional cut for the observed forbidden profile. It returned eligible candidates with six and eight holes, then `UNKNOWN` in an exact neighborhood. It did not improve the eligible seed. The short smoke test used a 0.1-second solver budget.

For a fixed disjoint five-triple profile, the wrapper defines exact threshold indicators `six_i = (multiplicity_i >= 6)` and `seven_i = (multiplicity_i >= 7)`. The inequality `5 * sum(six_i) + sum(seven_i) <= 26` excludes exactly the forbidden condition. Each indicator has both directions encoded. These cuts are necessary for full 64-block covers under the independently proved profile theorem; applying them to partial candidates is an explicit construction restriction. New forbidden profiles are rejected and saved as cuts for the next neighborhood.

All 243 combinations of counts below six, equal to six, and at least seven passed a direct row and hint truth-table check. Regression controls reject the actual three-hole candidate and accept the structured six-hole escape. Every returned candidate was checked by both cover verifiers. Auxiliary hints were recomputed from the retained blocks and actual sparse block-variable hints, checked against each conditional cut, and recorded per attempt.

`campaigns.json.gz` preserves all three runs' metadata, frozen source snapshots, result records, candidate texts, postchecked profiles, and hashes of every saved file. `campaign-manifest.json` gives the archive hash. Large models and solver logs remain in ignored scratch. The source in this directory includes the corrected predicate and conditional cuts; the archive preserves the earlier source as it actually ran.

The observed results concern only the recorded retained-block neighborhoods. Timeouts are inconclusive. The stopped run and its rejected partial candidates provide no impossibility proof.
