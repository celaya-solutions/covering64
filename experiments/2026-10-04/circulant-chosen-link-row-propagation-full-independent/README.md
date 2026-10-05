```text
Document:    Independent Full Row Propagation Launch Gate
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      d3c5e8dd5ac9ce47130832b23138037b2bff4643620110369f59439cad7d2a25
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent launch gate

GO for exactly one full finite row-propagation pass over the 10,228 saved
single-pass survivors, using the frozen runner and manifest identified in
`gate.json`. No optimizer, failed-literal search, retry, or automatic resume is
authorized by this gate. This gate review did not perform any real propagation,
start any process, or send any signal.

The gate binds the full runner, manifest, producer files index, all 22 manifest
dependencies, and the independent 1,000-case benchmark audit. That earlier audit
replayed 79,165 forcing steps, 893 contradictions, and 107 row-bound fixed points
using independent sets. The full runner imports the exact unchanged benchmark
propagator. Arithmetic conclusions from the full run still require a separate
replay of the saved full-run traces.

## Time and cursor checks

The worker starts its clock before input loading. It stops starting cases at
44.5 seconds and passes that same absolute deadline to the per-row propagator.
Its cooperative total budget is 45 seconds. The separate supervisor waits at
most 50 seconds before sending TERM to the child's isolated process group,
then allows five seconds before KILL. The cooperative budget is not a hard
45-second process deadline; the runtime receipt must report any overrun.

Each trace and survivor record is a complete independent gzip member. The worker
flushes each member before atomically replacing the cursor. Only the byte
prefixes named by the last committed cursor can be treated as saved evidence.
Extra complete or partial members beyond those offsets remain uncommitted tails.
The completed interval is exactly the half-open interval from zero to the saved
next-survivor index. An interrupted case may have a saved trace prefix but keeps
that same index uncompleted. Outcome counts include completed cases only; trace
steps and row visits also include a saved interrupted trace.

Atomic replacement and flushing protect the prefix across process interruption.
This review does not claim durability across power loss or storage failure.
A present terminal result must still parse and pass its runtime checks; file
presence alone is insufficient after a killed process.

## Mocked controls

Fourteen synthetic worker controls covered normal completion, cooperative
interruption, stopping before the first and second cases, a verified candidate,
candidate verification failure, interruptions before/during/after trace and
survivor writes, and interruptions immediately before and after cursor
replacement. Each control independently parsed only the committed gzip byte
prefixes and checked cursor counts, case order, survivor bindings, outcome and
step accounting, and candidate-verification receipts.

Five mocked watchdog controls covered normal exit, TERM, KILL, a TERM exit race,
and a KILL exit race. They checked the exact wait limits, isolated process group,
signal targets, final return codes, and status flags. Two mocked supervisor
controls covered normal and killed children, verified saved cursor/log hashes,
and confirmed that a second launch was rejected. All 21 controls passed.

The scope remains only the 10,228 survivors of the chosen four-witness image
catalog. A contradiction excludes its exact profile/partial completion case.
A row-bound fixed point is not a feasibility claim. No unrestricted covering
number or lower-bound conclusion follows from this gate.

## Reproduction

```sh
uv run python experiments/2026-10-04/circulant-chosen-link-row-propagation-full-independent/check.py
uv run ruff check experiments/2026-10-04/circulant-chosen-link-row-propagation-full-independent
```

The checker invokes runner functions only with mocked processes, synthetic
records, and temporary output directories. It never invokes the production
propagator, a solver, or the full production launch. Ruff passes.
