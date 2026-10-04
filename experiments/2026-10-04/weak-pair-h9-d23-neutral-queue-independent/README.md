```text
Document:    Independent H9 D23 Queue Delta Gate
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      a151f7b55488b7fcd6e7424d2d39a04da29bc15bc8f6c865bd461816d8c48d12
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent H9/D23 queue gate

**GO for one root-launched pilot**, bound to the exact manifest, runner, start, and binary hashes in `gate.json`. No production shell, native search, or optimizer was launched during this review.

## Focused checks

- Rehashed 1,411 unique input/source/artifact pins. Reused the original queue, resume, and native reviews by exact hashes; did not repeat the unchanged kernel or adapter audit.
- Matched the start `f5f24d57738763380c715769eef4328d7f1950a8ae6d0eedd8e9ff16dc3fc681` to the independent native runtime audit, including its IDs, weak metrics, package report, and standalone report. It has 64 distinct blocks, 9 holes, D2max 23, D2sum 29, minimum pair multiplicity 5, D3=D4=0, and four original core overlaps `[1,0,1,1]`. It is a checked partial, not a cover.
- Compared the queue AST with the audited resume queue. Its only semantic queue changes are the two constants reducing the center budget from 32 to 16. The rank, base-module loader, and shell adapter wrapper are identical. Direct source review confirms the fifth-core additions only record overlaps in persisted center and final-result metadata.
- Checked the singleton initial frontier and exact equality of the 34 historical hashes with the previous completed queue's visited set. Every historical witness is a distinct 64-block family; fresh counting gives replacement distance 63 from this start for all 34.
- At most 15 adopted one/two-swap transitions precede center 16, so every processed center lies at distance≤30 from the start. A final two-swap inspection gives candidate distance≤32. Since63>32, the pilot cannot reach a named historical center, even before its explicit visited-state rejection.
- The independently proved fifth core has initial overlap 1. Replacing at most 32 blocks raises that overlap by at most 32, giving `overlap≤33<56`. This budget bound applies to every inspected exact 64 candidate. The fifth cap is only reported; the existing four filters remain the only kernel core filters. No claim about other relabelings follows.
- Eleven fresh abstract queue cases passed: strict and neutral 16-center bounds, five invalid frontier/history controls rejected before any callback, sampled-frontier exhaustion, two incomplete-call stops, and immediate cover stop. Each budget case used exactly 32 fake callbacks and retained the popped next state in the unscanned frontier. No plateau-exhaustion claim is made.

## Bound budget

At most 16 centers and 32 sequential shells. Each shell has 120 seconds, a 135-second watchdog, and 5-second termination grace. The runner requires an independent GO binding, stops on a cover or failed/incomplete shell, rejects relaunch, and allows no budget transfer. The neutral sample retains at most 64 legal equal-rank families per shell in the already audited traversal. Lexicographic `(holes,D2max)` remains the rank; D2sum is diagnostic only.

`check.py` reproduces file bindings, start/receipt equality, history arithmetic, queue AST comparison, and the eleven abstract controls without launching any search. `checks.json` records the result. Ruff passed on the new checker. Its document-header hash covers the source body after the header.

The separate [post-March source refresh](../post-march-public-source-refresh/README.md) found a maintained successor repository and screened accessible recent primary abstracts. Its exact current target entry remains unverified after HTTP403. The March archive's 61–65 range is not asserted to be current; the bounded literature screen does not prove absence of later improvements. This limitation does not alter the internal correctness or scope of the bounded pilot.
