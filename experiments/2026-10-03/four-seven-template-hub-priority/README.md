```text
Document:    Combined Template-Hull and Hub-Count Priority Screen
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      8d8a8a9f3939388f0132fd82a811c8aea36d812b0e5cbf46eb331e189b843c64
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Combined template-hull and hub-count priority screen

The first template-hull screen leaves 153 original first-link types open after
105 checked exclusions. Among those survivors, 23 have independently checked
exclusions for five of the six exhaustive integer hub-count cases. This screen
solves only their remaining sixth case: 16 cycle representatives and seven
matching representatives. The frozen plan lists each ID and its five prior
case exclusions.

The remaining cases use `(m4,z)=(0,1)` or `(0,2)`. Here `m4` counts blocks
containing all four hubs and `z` counts doubled hub triples. Thus four reusable
models suffice: two hub-count cases for each of cycle and matching. Each
representative receives at most 15 requested solver seconds, shared between
feasibility and optional phase one; the campaign ceiling is 345 solver seconds.
Construction, audits, integer certificate arithmetic, and file writing are
outside that solver-time budget. There is no promise of a wall-clock ceiling.

## Model layout

Start with the frozen original-100 whole-template-hull matrix, unchanged. Append
exactly two hub equalities, using hub labels `{4,8,12,16}`:

1. The sum of the 12 block variables containing four hubs equals `m4`.
2. The sum of `choose(h,3) * x_block` over the 276 blocks containing at least
   three hubs equals `4+z`.

Then append the seven explicit first-link equalities `x_block=1`. Original
variables retain their `[0,1]` bounds, original objective fields, and original
order. The first 4,368 are the global lexicographic block variables, followed by
400 double-triple variables and the unchanged template weights. There are
4,559 rows: 4,550 original hull rows, two immutable hub rows, and seven resettable
first-link rows. Cycle has 104,848 variables; matching has 61,576.

Phase one softens only the seven first-link equalities, with 14 nonnegative
unbounded slacks and unit objective coefficients. Both hub rows and all hull
rows remain exact. Inherited solver, fixed-row clearing, reset, and certificate
utilities are loaded only after their frozen source hashes match.

## Preflight and provenance

The separate `preflight.py` makes no solver calls. It checks all eight
feasibility/phase-one layouts and 46 fixed/reset transitions. After deleting the
nine new rows, each full exported protobuf must match the earlier frozen hull
protobuf byte-for-byte. It independently enumerates the expected hub row
coefficients from the lexicographic blocks. It checks all domains, objectives,
seven fixed rows, slack signs, and rejection of unreset transitions. It rejects
92 damaged models covering changes to prior rows, variables, objectives, hub
coefficients/bounds, missing/extra rows, stale fixes, and phase-one slacks.

- Runner SHA-256: `9d4689c59d12c7326cf5a7e03cafe9d09eb7c5698db1f085446cd57d02fca661`.
- Checker SHA-256: `4cd207b45f00265d0bb9cc1f53ede0b572121f09405a84a9548e10b13749eee5`.
- Preflight result SHA-256: `5d7c96c780f2f2e8ab185205a96f01b32f47118e9e625214d358ff2b24c7ce94`.
- Priority plan SHA-256: `9653d367494c23fe4018990aa7ad142b1ccf9d0a495b634049f395a31912772c`.

The plan links the six independent hub-campaign audits, the independent
six-case partition audit, and the completed template-screen summary. All frozen
hull matrices, catalog manifests, and source hashes are checked again at load.
The parent agent reviews the prepared source and preflight before launch.

The plan's 522 unresolved conditional branches describe its frozen pre-repair
hub-campaign snapshot. Seven later independently replayed numerical repairs
reduce that count to 515, without changing these 23 priority representatives or
their remaining `(0,1)`/`(0,2)` cases. Those repairs are recorded separately in
`../four-seven-hub-count-screen/numerical-repair-audit.json`.

## Planned command

```sh
uv run python experiments/2026-10-03/four-seven-template-hub-priority/run.py \
  --output experiments/scratch/four-seven-template-hub-priority-20261003 \
  --preflight experiments/2026-10-03/four-seven-template-hub-priority/preflight.json \
  --seconds 15 \
  > experiments/2026-10-03/four-seven-template-hub-priority/run.log 2>&1
```

The output must be new. Every attempted representative retains its exact fixed
rows, combined base matrix identity, raw solver logs, timings, reset audits,
and any sparse primal, dual, or integer certificate attempts. Source revision,
solver version, commands, input hashes, and frozen source copies are saved.

A positive certificate remains pending until independently replayed. Excluding
a first-link type requires that checked sixth-case certificate plus the five
previously checked conditional certificates and the independently audited
exhaustive hub partition. Numerical feasibility and timeouts remain inconclusive
for covers. A near-integral selection must pass both covering verifiers. No
unrestricted lower bound is claimed. No external research source is needed for
this finite model-combination experiment; all proof dependencies are local
frozen artifacts linked above.
