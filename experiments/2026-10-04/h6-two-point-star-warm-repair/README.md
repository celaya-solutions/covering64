```
Document:    H6 Two Point Star Warm Repair Preparation
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      3a11faa5107e4a45bf34f18fab8ff6a3aa88b45281ec263f6af056ee3e58fe08
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Warm continuation of the H6 two-point star

Prepared for independent root review; no production optimization is authorized
by this preparation alone. The original runner, model, and UNKNOWN result remain
unchanged. The prior call found no candidate.

This continuation uses the independently checked anchored H9 family a579aa… as
a complete feasible hint. It differs from the H6 family in four blocks, all of
which touch point 6 or point 10. Every outside-star membership is unchanged:
2,002 fixed block variables, 30 fixed selected blocks, 2,366 free variables, and
34 selected free blocks under the exact64 requirement.

Only the last model row changes, raising the hole ceiling from six to nine.
All 560 exact hole flags, all 120 pair-floor-five rows, the exact64 row, all
variable domains, and the minimize-holes objective remain unchanged. Replacing
the hint and restoring the old ceiling must reproduce the original proto exactly.
The only parameter-file change is seed 2026106001 to 2026106002.

The new hint has 64 distinct blocks, nine holes, pair floor five, and no violated
model row. It is a partial family, not a cover. It retains D3=1 and is not
weak-qualified; the model deliberately contains no D2/D3/D4, core, degree, or
rotational restrictions. The purpose is to allow descent from a feasible H9
hint under the same outside-star memberships.

The thin adapter imports the pinned original star runner and remaps only its
output paths, input metadata, seed, revision, and module file path. Its existing
preflight, child, process, vector-validation, and dual-verifier function bodies
are reused unchanged. The remapped module file path makes child dispatch re-enter
the adapter and makes preflight bind the adapter's hash. The unchanged base runner
is separately pinned as a dependency.

The proposed budget is one 120-second call, four workers, seed 2026106002, with
a 140-second parent watchdog and five-second termination grace. No retry,
extension, or budget transfer is allowed. Root alone reviews and launches it.

Preparation saves complete hint validation, unchanged-outside-membership proof,
and exact model/parameter delta evidence. Controls use mocked processes and
mocked solver responses only: normal exit, terminate, kill, repeat rejection,
UNKNOWN without a solution, feasible H9 vector saving, and atomic callbacks.

After an independent GO gate is frozen, root may use:

```sh
uv run python experiments/2026-10-04/h6-two-point-star-warm-repair/run.py --execute PATH_TO_GATE
```

A result concerns only this fixed neighborhood. UNKNOWN/timeouts are inconclusive;
CP-SAT INFEASIBLE is not an independently checked local or global theorem.
