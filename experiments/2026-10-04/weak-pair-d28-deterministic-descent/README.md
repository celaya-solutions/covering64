```
Document:    Bounded Deterministic Weak-Pair Descent
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      105fe538ecfa15aa6a3cf28a7aacefdc2501aeaa08c0db4e998cbc953855c841
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Prepared campaign, not launched

This wrapper starts from the preserved D28 representative, SHA256 `c6d132069270ead505488fa863a12a0f16a82e289c989a1c4d5961b13826e06f`. It has 64 distinct blocks and H12/D2max=D2sum=28, with pair floor five, zero D3/D4, and four named core overlaps `[1,1,1,2]`. Preparation rechecks it with both verifiers and both unchanged recorder implementations. No scan, solver, or compiler is called during preparation.

There are at most four rounds. Each round first scans the exact-distance-one shell, then the exact-distance-two shell, from the same unchanged center. The existing binary bytes and validated recorder functions are reused; no search kernel is added or changed. Each shell gets its own fixed 120-second budget, 135-second outer watchdog, and five-second termination grace. There is no restart, fifth round, time transfer, or budget transfer.

If both shells finish and have strict improvements, selection first minimizes `(holes, D2max)` across all tied best families from both shells. Among families with that best rank, it chooses the lexicographically least sorted 64-element block-ID list. It does not use exchange ordering, the first recorded tie, or the distance of the winning shell. That family becomes the next center only after a fresh recount and package/standalone verification. Every selected center must satisfy the same pair floor, single-triple rows, quadruple rows, and four named core caps.

No strict improvement after both complete shells stops the campaign. This certifies only that the named rank cannot improve within those two shells around that exact center under the fixed filters. It says nothing about multi-step paths through equal or worse ranks, other centers, or the unrestricted covering problem. Reaching round four also stops, even if a strict improvement was selected there.

Any incomplete or invalid shell stops the whole campaign without adopting a partial next center or claiming local closure. Raw output is always retained. Complete recoverable candidate observations are reconstructed, recounted, and dual checked even if the terminal record is damaged; they cannot support a neighborhood-best claim. A dual-verified cover may stop the campaign early. If the other shell was not completed, the cover is kept as an existence witness without a completed-round tie choice or optimum claim. Incomplete status is retained when the shell itself was incomplete.

The shell proofs remain unchanged: every distance-one family has one unique outgoing/incoming pair, and every distance-two family has one unique sorted outgoing pair and sorted incoming pair outside the round's original center. Pair-floor pruning recomputes the remaining pair deficits for the current center, then retains exactly the completions containing their required endpoints. It does not require intermediate partial swaps to pass weak rows. Every completion still receives the same final weak-row and core-cap checks. These are neighborhood arguments, never reductions of the unrestricted model.

The wrapper adds strict event grammar and finite-time checks before reusing each recorder's validation. Every saved improvement record and best tie receives a canonical witness and full dual-verifier receipt. Each shell records the center, binary, recorder, command, budget, watchdog state, logs, candidates, and hashes. Selected centers and round outcomes remain reviewable; raw logs, binaries, source snapshots, complete tie receipts, and large artifacts stay in ignored scratch.

`controls.json` contains fake-shell and fake-process checks for same-center sequencing, full-family tie selection, first/second incomplete outcomes, malformed events, cover-only early stops, the four-round cap, and both watchdog termination paths. These controls invoke no search binary. Root alone may launch after an independent gate binds the final manifest, runner, starting family, and both binary hashes.
