```text
Document:    Independent Circulant Exact Profile Runtime Replay
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      42101695f26ff5f93de220ec700f537d1b6fb9cdb1c362d11232b3ce2e20f160
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent eight-profile runtime replay

All eight saved response protobufs, solver logs, embedded child receipts, commands,
parameters, model bindings, and frozen input hashes pass replay. Every solver returned
UNKNOWN. No candidate vector or witness exists. These timeouts are inconclusive and
do not exclude any of the eight profiles.

The total native solver time is 240.003671 seconds. The eight recorded process times
sum to 244.470449001063 seconds. The producer's whole wrapper elapsed
time is 244.48303966701496 seconds. All child return codes are zero, captured stdout
and stderr are empty, and no watchdog, termination, or kill occurred. All eight runs
completed in the prepared order with seeds 2026106401 through 2026106408, one worker,
and 30 seconds each. No retry, budget transfer, or extra optimizer call occurred in
this audit.

The checker rehashes all 27 preparation pins and binds the launch/result to the exact
GO gate and audited manifest. It verifies the raw-file index for every case, parses
response protobufs independently, checks logged model dimensions and parameter values,
and compares final status and counters with each response. The eight models still have
4,368 free Boolean block variables, exact64, and 560 exact profile rows only. No fixed
link, neighborhood, or block-family invariance is added.

The candidate path checks any future terminal vector for strict Boolean type, exact64,
all560 exact triple demands, response/vector agreement, canonical witness bytes and
hashes, and both cover verifiers. Seven malformed vectors are rejected in this audit.
There is no positive64-candidate control because this batch produced no candidate;
no claim to have verified a nonexistent witness is made. The verifier code hashes are
among the frozen preparation pins.

This audit performs no optimizer launch or native requery. UNKNOWN remains inconclusive;
INFEASIBLE in another run would require a separately checked proof for a mathematical
exclusion. The eight fixed profiles include four reflection pairs. Other excess profiles
for the same circulant graph and unrestricted C(16,5,3) remain unresolved.

The receipt is frozen and the checker refuses to overwrite it. Source, result, gate,
launch, model, parameter, and raw-output hashes are recorded in review.json and files.json.
Ruff passes.
