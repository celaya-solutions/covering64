```
Document:    Independent Fixed-g1 Presolve Diagnostic Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      cc9e009e03f6b3dc3c18b9abcb7fffd247f1eb658c329b8749c87544ddcf5c2d
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Fixed-g1 presolve diagnostic audit

The delta gate binds the previously reconstructed 276-variable, 1,977-row model,
all original input hashes, and two exact parameter files. Both cases allow ten
seconds, one worker and seed 2026104070; only the presolve Boolean differs between
them. The model and objective remain unchanged. Each distinct registry-accepted
tuple can receive at most one one-second completion LP.

Both master responses reported OPTIMAL at distance six from the saved baseline.
Normal presolve took 6.360403082915582 seconds and produced a registry-rejected
candidate. Presolve off took 2.0344423750648275 seconds and produced an accepted
candidate. Its one LP reported OPTIMAL at 13.514017967610794; the independent
primal recount was 13.514017967611121. The incumbent remains 7.52051548546158.

The independent readback matches both model copies, parameter and response
protos, all registry transports and proof sources, completion rows, numerical
primal/dual hashes and the primal residual. Total solver time was
8.519048416055739 seconds; wall time was 9.960837500053458 seconds. No fractional
completion, integer cover, new exact separation or improvement was claimed.

These two timings are individual diagnostic observations, not a general speed
comparison. OPTIMAL distances are solver reports for this finite master and are
not independently checked proof certificates. No optimizer is called by either
audit script. Frozen receipts are never overwritten.
