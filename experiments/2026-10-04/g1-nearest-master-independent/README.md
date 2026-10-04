```
Document:    Independent Fixed-g1 Nearest Master Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      ba27facf46a3bc16090cce8e2fc847f398f868adf58b7b2323e16c29d0b996e0
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Fixed-g1 nearest master audit

The preparation gate rebuilds the complete 276-variable, 1,977-row master from
605 structural rows, 353 broad planes, 1,000 separately checked g1-only planes,
and 19 seven-block graph-one registry nogoods. It checks both transports and
proof references for each registry nogood, the frozen baseline primal, and the
fixed overlap objective with no radius constraint. Two damaged models are rejected.

The authorized campaign made one two-second master call. It returned UNKNOWN,
with no candidate and no completion LP. Solver time was 1.985302958986722 seconds;
wall time was 3.33435866702348 seconds. The independent readback matches the saved
master, parameter and response protos and all raw hashes. No new cuts or registry
nogoods were produced. The result is inconclusive.

No optimizers are called by these audit scripts. The postcheck exercised the
actual UNKNOWN/no-candidate path; candidate/LP branches are not claimed as tested
by this run. Frozen receipts are never overwritten.
