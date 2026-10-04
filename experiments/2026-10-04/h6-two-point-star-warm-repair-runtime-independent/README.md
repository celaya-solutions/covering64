```
Document:    Independent Warm Star Runtime Result
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      90bc4d3b9e9d86457fc2ec730c1246a6a53be0960a17ade28a8fd8c2e7026798
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Checked result: unchanged H9 partial

The sole warm-star call returned FEASIBLE with objective 9 and bound 0 after
120.00696 solver seconds. The wrapper completed normally without its watchdog.
One callback and the final vector are both the same input family
`a579aa1176b5ab073db53208f3e2055df01b848fd82db94866ff870835428f05`.
There is one unique saved family and zero new saved families. No improvement
or cover was found.

The independent replay checks all 14 raw-file hashes, gate and model bindings,
the frozen parameter file, launch dispatch, every vector domain and active row,
the final solver response, and both cover verifiers. It independently recounts
the candidate metrics: H9, minimum pair count 5, D2max 21, D2sum 38, D3 1, and
D4 0. The six named overlaps are [0,2,2,1,0,0], so all named caps pass. The
family is not weak-qualified because D3 is nonzero. Four damaged-vector controls
are rejected. No solver or native search runs during replay.

The H9 input is feasible in this model but is a partial family, not a cover.
The prior H6 call remains a separate UNKNOWN result with no saved candidate;
its reported objective 6 is not an incumbent and is not a comparison result.
This outcome concerns only the fixed outside-{6,10} memberships with H<=9.
It gives no unrestricted lower bound, nonexistence result, or novelty claim.

Producer result SHA256:
`b75aeabe07e529dd3e5318d95e433021bb38b2c8dc19e10de7c4c2b2e6bd46ff`.
Independent receipt: `postcheck.json`.
