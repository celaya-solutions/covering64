```text
Document:    Independent Seven Affine Completion Runtime Replay
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      40bb95d96228d82626883b31b87c5abc4c2423ed3321fcd20fdd1082c1dffe42
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent completion-runtime audit

All seven saved worker results, solver logs, parameter records, and frozen model bindings
pass independent replay. Every worker reports INFEASIBLE during presolve, with zero
branches and conflicts. No witness, values file, or candidate-verifier output was produced.
The worker exit codes are all zero because each worker successfully saved its result;
this does not mean the mathematical model was feasible.

The total reported solver wall time is 0.061004 seconds. The seven worker process times
sum to 2.357667623087764 seconds. No process watchdog or kill was recorded. All seven
logs show the exact intended seed, 30-second limit, and one worker. They show 4,368
Boolean variables, 1,365 singleton rows, and 561 other linear rows with 48,048 terms.
The final response text in each log agrees with its result JSON. Floating-point wall
times are compared within 1e-9 relative or 1e-12 absolute tolerance, allowing binary
representation differences such as 0.008974000000000001 versus printed 0.008974.

The audit rehashes all 54 frozen preparation/dependency files and binds the root launch
record to the independent GO gate, exact manifest, runner, model-gate review, and start
marker. It checks seven ordered receipts and exactly seven output directories, plus
all stdout, stderr, and result hashes. Every stderr is empty. Sixteen malformed runtime
controls are rejected. The checker imports no solver or process module and launches
nothing. Ruff passes.

These are seven conditional solver statuses, not independently certified mathematical
exclusions. No proof certificate accompanies them, and this audit checks no such proof.
A separate finite exclusion certificate may later settle these exact branches; it must
be reviewed separately. The previously checked 249 finite exclusions remain distinct
from these seven CP-SAT outcomes.

The ordered receipts and previously audited sequential runner support the recorded
call order. They do not include separate absolute start timestamps for each child.
Nothing here excludes another local link, affine embedding, recipe, or unrestricted
64-block cover. The earlier complete 65-block cover is unrelated to these partial links.

The checker refuses to overwrite its independent receipt. Use a fresh sibling directory
for another saved-only replay. The review and file index carry all artifact hashes.
