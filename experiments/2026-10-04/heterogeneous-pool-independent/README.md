```
Document:    Independent Heterogeneous Pool Gate
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      d25c5661e9d419f87f5e333ed6b86c54c21366dae9a66f07a0ea1a78b958453b
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent pool gate

Both prepared models exactly match an independent reconstruction of every protobuf field. Each has 4,368 lexicographic block Booleans, 560 hole Booleans and 1,122 linear rows. The rows enforce exactly 64 blocks, zero selected blocks outside the named pool, and the exact equivalence between an uncovered triple and its hole variable. The objective is the sum of the 560 holes. No degree, hub, link, graph or symmetry condition is imposed.

The ten copied seeds were freshly checked by both verifiers and separately recounted. Their union has 277 blocks; the second pool has 337. The 60 additions were replayed from the saved seed against the sorted complement. Every source seed fits both pools. Both complete hints satisfy every model row and have three holes. The gate checked source budgets of two cases, 30 seconds each and four workers. No optimizer ran during this audit.

Nineteen damaged controls were rejected, covering block count, duplicates, malformed labels, model cardinality, membership, coverage, hole polarity, hints, objective weights, variable domains and block order. All source profiles, support histograms and pairwise common-block counts are retained in `gate.json`. This GO applies only to the frozen manifest and these two restricted pools.

## Completed response replay

The two runs each had a 30-second, four-worker solver limit. Both returned FEASIBLE, objective 3 and numerical bound 0. Thus the pilot found no lower hole count and did not establish the restricted optimum.

Each callback saved the original three-hole hint. Each final CP response instead contained a different equal-objective state. Both final states have been extracted, checked against all model rows, independently recounted, and run through both covering verifiers. Their degree histogram is 19:2,20:12,21:2; pair histogram is 4:1,5:90,6:17,7:12; triple histogram is 0:3,1:498,2:54,6:1,7:4. Both contain the original saved 60-block core exactly. None of the ten source seeds matches all three histograms, but no core escape occurred.

`postcheck.json` records both complete response replays, all raw hashes, five damaged-response controls, exact final profiles, saved-seed overlaps and checked core overlaps. The final states are `elite-final-response.txt` and `expanded-final-response.txt`. The strict-improvement callback intentionally ignores equal-objective ties, so the final response must be inspected separately.
