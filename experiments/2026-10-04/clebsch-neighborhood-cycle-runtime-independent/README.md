~~~text
Document:    Independent Clebsch Cycle Runtime Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      fc499815632b20cbfaa1946a6b0b2fa2eed4cc764956730538746f602ffa9d19
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
~~~

The single authorized CP-SAT call returned INFEASIBLE during probing in presolve.
This is a checked record of a solver response for the fixed sixteen-neighborhood
plus cycle construction. It does not supply an independently checked
infeasibility proof and does not establish a global lower bound.

All six original manifest pins and all seven runtime files match their saved
hashes. The launch marker binds the approved gate and manifest. The response,
solver log, child receipt, and wrapper receipt agree. The native wall time was
0.015652 seconds; solve elapsed time was 0.018310290994122624 seconds; the saved
process-wrapper elapsed time was 0.7592483749613166 seconds. The process exited
zero with no watchdog, termination, or kill. Both captured output streams are
empty. No witness or solution vector was written, and the response has no
solution or additional solution.

Seven changed-result controls are rejected: bad process exit, watchdog flag,
complete64 claim, independent-proof claim, response status, invented solution,
and native-time mismatch. The audit imports neither the producer nor its solver
entry point and makes zero optimizer calls. Ruff passes.

Replay with:

~~~sh
uv run python experiments/2026-10-04/clebsch-neighborhood-cycle-runtime-independent/check.py
~~~

The audit SHA256 is
19cbbb5da1c67088a4ab5a5e1b7c540b22f8f222b8483dc8236a210b3810fe45.
The producer result SHA256 is
cb547ca75bf8d4e8d264c0fe80cb9f564231fbb2c289fce50acb4185ca792bf3.
