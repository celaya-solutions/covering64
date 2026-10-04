```text
Document:    Whole-Template-Hull First-Link Screen Launch Record
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      8cacfc4d13b64eb5f25eb2730569bf48791c14be48c9e55805445d422ff83071
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Whole-template-hull first-link screen

This campaign tests the 156 first-link representatives that remain after the
original 100 exact LP exclusions and the two independently replayed blossom
exclusions, `matching-038` and `matching-051`. It uses the frozen **original-100**
whole-template-hull matrices; it does not rebuild catalogs using the later
exclusions. There are 102 cycle representatives and 54 matching representatives.

Each feasibility model is the independently audited 4,550-row extended matrix
plus exactly seven equalities `x_block = 1`. The original variables keep their
`[0,1]` domains and their original order. No incidence, symmetry, objective, or
other rows are changed. Templates describe every allowed labeled heavy link;
the model does not assume that an integer cover is invariant under a relabeling.

## Frozen sources and preflight

- Runner `run.py`: `c8841227df38eec07b28f9776e812e1df4c8c4175e80c0feead9fb15f8289b9e`.
- Reset checker `preflight.py`: `d44bcd672074ba3b50c330161816ba5dec397b5426c6502d7f53e6d1ebcccfe4`.
- Preflight result: `dc1dd91cc3b505229daabe266e7136479d6c05b1bebf823662da81ed3d1605e7`.
- Whole-hull utilities: `c6b67b22660707c701ae038db497e81fded3c647e9f1978873b5e27da573afcf`.
- Original hull manifest: `21c243c87f44aebe780d8a48e330684d5fcaefbc2a587fa236516d64d8cfc38a`.
- Representative selection: `27c0e77561c37b86dd60b85427256b30f6ce9433a87edd39c41ed73dc69e601d`.
- Independent matrix audit: `fe57e7e414426f9d9c5815d062aa82b56f363408582d8d88dc40967f1f2df7ef`.

The preflight exercised all 156 representatives on both the feasibility and
phase-one models: 312 fixed/reset transitions, 42 rejected damaged controls,
and zero solver calls. It checked full original-model protobuf prefixes,
fixed-row coefficients and bounds, objective fields, and slack domains and
signs. `Constraint.Clear()` removes old coefficients before reuse; coefficient
assignment to zero alone leaves entries in the exported protobuf. Each live
solve repeats the fixed-state and reset audits.

Phase one adds exactly 14 nonnegative unbounded slacks, with unit objective
coefficients, to soften only the seven fixed equalities. All original matrix
rows remain exact. Its integer certificate attempts apply to the unsoftened
matrix plus the seven original fixed equalities.

## Launch and budget

The parent agent authorized launch after reading the frozen preflight. One
process runs both cases, with at most 15 requested solver seconds per
representative, shared between feasibility and phase-one certificate
extraction. Model construction, state audits, integer certificate arithmetic,
and file writing are outside that solver-time budget. The measured durations
are saved, so any solver return-time overhead remains visible.

```sh
uv run python experiments/2026-10-03/four-seven-template-link-screen/run.py \
  --output experiments/scratch/four-seven-template-link-screen-20261003 \
  --case both --seconds 15 \
  > experiments/2026-10-03/four-seven-template-link-screen/run.log 2>&1
```

The output directory must be new. Frozen source copies, solver version, source
revision, commands, base sparse matrices, base protobufs, and input hashes are
saved in that directory. Each representative retains its exact seven rows,
native logs, solve times, reset audits, and any sparse lossless primal or dual.
Certificate rounding tries denominators one million and one billion.

## Interpretation

A numerical feasible result is not an exact covering witness. A timeout or
unknown result is inconclusive. Solver infeasibility alone is not an exclusion:
positive integer certificate attempts are marked pending until an independent
checker replays the full matrix, variable bounds, and certificate. A near
integral block selection must pass both the package verifier and the separate
standalone checker. No global lower-bound or covering-number conclusion follows
from this campaign without the complete reduction and proof chain.

This launch note records setup only. Campaign results and independent replays
will be written as separate artifacts to preserve the frozen evidence.
