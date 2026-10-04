```
Document:    Hard Top-Two Runner Preparation and Controls
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      cd7298e374dc7a1fe05ec75037149d62314ad90080f33c4fb7102126eac7b0fd
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Separately frozen hard-model runner

The model preparation manifest remains unchanged. `runner-manifest.json` adds
the later-authorized runner without replacing the frozen model or its proof
bindings. The runner is prepared but unrun. No optimizer has been invoked.

`execute.py` requires an independent JSON gate with passed=true and decision=GO,
an explicit expected gate hash, and the --execute flag. Its gate must bind
manifest_sha256, model_sha256, parameters_sha256, guidance_sha256, runner_sha256,
and runner_manifest_sha256. Current sources, proof receipts, core supports,
model, parameters, guidance, and actual H49 candidate are hash-checked before
the solver can be reached. It refuses an existing run directory or result.

The sole prepared run is120 seconds, four workers, seed2026104601. The objective
is holes only. H49 remains explicitly infeasible block-only guidance, with no
complete feasible warm start. Every delivered callback is saved, including any
ties, without filtering; any feasible final vector is saved separately.

Each state is checked against all serialized variable domains and active rows.
Its first5,608 entries are matched against direct block/count/hole recounts.
The actual z/y values need only satisfy the rows; the runner also saves the
canonical second-largest-threshold extension, without requiring solver z/y to
be canonical. Full raw vectors, canonical vectors, block witnesses, metrics,
all-pair details, and both covering-verifier reports are retained and hashed.

The runner stops only on actual zero holes after both covering verifiers agree
that the family is a cover. Nonzero-hole feasible states remain valuable hard-D2
hints, not covering witnesses. The final result records status, one optimizer
call, first feasible time, elapsed/solver times, callbacks, bound, raw file hashes,
and gate/source/manifest bindings. UNKNOWN remains inconclusive.

`check_runner.py` exercised the real serialized-row evaluator and pre-run
rejection paths. H49's canonical extension was rejected for a budget violation;
a damaged Boolean domain was rejected; NO_GO and incorrectly bound gates were
rejected before the runtime directory was created; and the existing-directory
rule rejected relaunch. The controls made zero optimizer calls and wrote no
hint. No accepted hard-family path could be exercised because no such family
was available. Independent review of the runner remains the launch gate.

Frozen bindings:

- `execute.py` SHA256 `bd3ee87c19233ecdc916700cbc64f22d7435bea302906dec607fc48cebaf7470`.
- `runner-manifest.json` SHA256 `48397e1767b00b5a1fd9519fe98a7af5af19f1906f3b2e82a145c98083cdfe2d`.
- `runner-controls.json` SHA256 `c4b1ac4c6294d2e787949440714a717b103b04b8bf2edb91bb52418048a6ed1a`.
