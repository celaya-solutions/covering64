```
Document:    Native Compact Pair-Two Pilot Independent Outcome
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      fed2dcb4dcbe9351da5aa8b50126e9442b17b89f031c63ca991e321f6a4b4337
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Native compact pair-two pilot outcome

Both declared native calls finished normally. Neither found D2max=0, so no qualified hint or cover was obtained. The campaign stopped after its two allowed budgets with no skipped runs, watchdog intervention, validation error, or budget reallocation. The outcome is inconclusive about existence of a 64-block cover.

| Seed | Best primary D2max | Primary holes | Primary D2sum | Primary D3 | Primary D4 | Minimum pair count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026104501 | 46 | 33 | 267 | 28 | 24 | 4 |
| 2026104502 | 56 | 59 | 510 | 52 | 48 | 4 |

The first run's raw best is the same H33 family as its primary best. The second run's raw best has 47 holes, D2max=75, D2sum=165, D3=D4=0, and minimum pair count five. These remain separate records. A lower positive D2max need not lower D2sum or preserve the weaker-cut scores; the zero equivalence remains exact.

Seed 2026104501 used 60.004894 seconds of measured process wall time and reported 60 native seconds over 126,405,504 iterations. Seed 2026104502 used 60.005936 seconds of measured process wall time and reported 60.0008 native seconds over 128,184,032 iterations. The nominal native budgets were 60 seconds each, and the small measurement/check-interval excess is retained in the raw logs.

The independent postcheck recounted all saved states and ran both the package and standalone verifiers for all 115 unique families, for 230 verifier calls. All are valid distinct 64-block families but noncovers. Final current states, which may be worse than their best records, are preserved and checked. All four core caps hold. Every record metric, strict improvement order, final saved file, source/binary binding, actual call count and stopping reason agrees with the frozen runner result.

`postcheck.json` contains the exact state and verifier bindings. `postcheck-manifest.json` binds this outcome without changing the pre-run gate or its manifest. The independent audit made no optimizer calls and authorizes no extension.
