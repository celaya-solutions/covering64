```text
Document:    Independent Hole Priority CP Runtime Postcheck
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      195d9a46416bb45947ffc0a8d1cd6ed419734470c3a26b008ff899e225278ba8
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent outcome

The one authorized hole-priority CP call ended FEASIBLE after 300.01341 solver
seconds, with 4 workers and seed 2026105001. Both callbacks and the final state
retain 12 uncovered triples. Actual compact and full-row pair deficits decreased
from 32 to 31. No cover or positive-hole actual-D2zero state appeared.
The reported objective bound is 0; it gives no covering-number lower bound.

| State | Holes | Actual D2max / D2sum | Solver deficit sum | Canonical / solver objective | Slack |
|---|---:|---|---:|---|---:|
| Callback 1 |12|32 /32|32|184364 /184364|0|
| Callback 2 |12|31 /31|31|184363 /184363|0|
| Final |12|31 /31|31|184363 /184363|0|

The final family SHA256 is
`a00c567a97a00429063ec599728e8b16fe3ed2c230c9eaffdf99939d7632563c`.
Both unique families have minimum pair count 5, D3=D4=0, four core overlaps
`[1,1,1,2]`, and profile maximum 0. These checks do not fill their 12 holes.

# Objective and stopping audit

The exact solver objective is `15361*holes + sum(solver d_P)`. All 120 deficit
variables lie in 0..128, so their total upper bound is 15360. Thus one fewer hole
has priority over any permitted deficit change. The independent checker
recomputes actual per-pair top-two deficits from block counts and keeps them
separate from permissible solver slack. A positive-slack control increases the
objective by 1 without changing the actual family. No observed vector has slack.

The checker independently confirms that the producer's stop flag means a
real cover checked by both verifiers. A positive-hole actual-D2zero state is
classified separately and does not trigger that stop. Callback ordering and
final-response agreement pass. No such partial zero state occurred in this run,
so the conditional hard-model qualification is not triggered.

# Evidence checked

All three saved 5,728-entry vectors pass every integer domain and all 14,405
model rows, including all 13,845 active rows and enforced hole channels.
For each vector, the checker independently reconstructs pair/triple/quad counts,
all 10,920 expanded deficits and their 120 compact maxima, holes, D3, D4, core
counts, profile maximum, canonical auxiliary values, and objective. Final vector
values exactly match the solver response. Both unique families pass the package
and standalone verifiers with actual count 64 and correctly remain incomplete.

Input/model/parameter/source/proof, gate, result, vector, witness, receipt and
raw-log hashes match. The solver log contains exactly one solver start and one
response summary. The 8 damaged-vector controls reject malformed/domain/count/
channel/deficit/cardinality errors; the valid positive-slack control passes.
No optimizer was called by this audit. Scoped ruff and diff checks pass.

Postcheck SHA256:
`7d75f7a3e30bd8587727c6b6f90ff8702e15b1e092914866246bf647d699e9be`.
Result SHA256:
`2be90db6cca1297d732e32b888c87887b2eda7344ac619743899173d2f2aed75`.
Gate SHA256:
`e6eba94f19dcb3af6402f0dc65b8a451e74b8f22205c34a40e0d976b284930fd`.
The audit preserves every producer file and makes no global infeasibility claim.
