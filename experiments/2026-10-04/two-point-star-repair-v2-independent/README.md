```
Document:    Independent Two-Point-Star V2 Model Gate
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      5e0e4d95ebeab316c46ef238c6176e75c0a8d8cbebdbb592213b3cc0da22abbf
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Exact model audit

The independent v2 gate passed. `gate.json` SHA256 is
`4856537e48cef8623b46a0abe6cd005e9f67deec67d3c02b0ddb9945208ed552`.
It binds manifest
`39e895e1bc69b5bc7295460f1151cd951c4c06c1e5691a1a90482b26d0807f74`
and the corrected producer source. No solver was launched by this audit.

Both models contain the full lexicographic 4,368 block variables and 560 hole
variables. For each pivot pair, the 2,002 blocks disjoint from both pivots have
fixed incumbent membership domains; the remaining 2,366 variables are free.
The checked D26 incumbent has 29 selected fixed blocks and 35 selected free
blocks. The models have exactly 1,242 linear rows: one exact-64 row, 1,120 hole
channel rows, 120 pair-floor rows, and one at-most-12-holes row. Every variable
name, domain, incidence coefficient, enforcement literal, row bound, hint,
and objective coefficient was checked from independent combinations.

For each triple, h=1 enforces coverage count zero and h=0 enforces coverage
count at least one. Since h is Boolean, these implications make h exactly its
uncovered indicator. The objective is the sum of all 560 indicators. Pair count
at least five is necessary for a cover because its 14 containing triples require
at least ceil(14/3) selected blocks through that pair. Fixed outside-star domains
are an explicit neighborhood restriction, not an unrestricted safe reduction.

Both incumbent assignments passed. Twenty damaged assignment controls and
20 damaged model controls were rejected across the two models. These include
the exact fractional-hole counterexample accepted by the preserved original
checker, float and Boolean vectors, damaged lengths, wrong hole labels, fixed
membership changes, weakened rows, altered objective coefficients, and added
assumptions. All controls were direct finite checks without solving.

The allowed campaign consists of two fixed runs from the same D26 center,
using pivots (6,14) then (1,9), 60 seconds and four workers per run, fixed seeds
2026105301/2026105302, and an 80-second watchdog plus five-second grace. A cover,
timeout, or process failure stops later launches. Callback and final witnesses
must pass both covering verifiers. No D3, D4, or core constraints are imposed;
partial candidates require those diagnostics separately. UNKNOWN/timeouts are
inconclusive, and CP-SAT INFEASIBLE is not an independently checked theorem.
The audit supports neither a global lower bound nor an unrestricted existence
conclusion.
