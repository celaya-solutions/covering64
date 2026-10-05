```text
Document:    Full Bounded Row Propagation for Chosen Circulant Links
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      6c9ab941afe327d0dee3e4dfb95c674080b797e60473e1ca9098fb5a93719d19
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Prepared full pass; root review required before launch

This sibling imports `circulant-chosen-link-row-propagation/run.py` and calls its
frozen `propagate` function unchanged. Each of the 10,228 saved single-pass
survivors starts again with all 3,003 pentads avoiding point 1 free. It rebuilds
the exact 455 outside-triple residual equations and the exact cardinality 44 row.
There is no failed-literal probing, optimizer, randomized choice, retry, or
automatic resume. The scope remains the images of four particular point-link
witnesses, not every possible point link or every affine construction.

The earlier deterministic 1,000-case benchmark completed in 1.738119 seconds:
893 contradictions and 107 row-propagation fixed points. Its measured full-pass
estimate was 16.531510 seconds; this is not a timing guarantee. The benchmark
source, manifest, results, trace, full single-pass survivor input, catalog,
verifiers, and this runner's preparation sources are pinned by SHA-256.

## Bounded execution

Only root may launch after reviewing the frozen code and independently replayed
benchmark traces:

```sh
uv run python experiments/2026-10-04/circulant-chosen-link-row-propagation-full/run.py run
```

The worker has a 45-second cooperative total budget. Both the stop-new-case and
per-row deadline are 44.5 seconds, leaving 0.5 seconds for final output. A sole
supervisor independently waits at most 50 seconds, then sends SIGTERM to the
child process group. It allows 5 seconds for termination before SIGKILL.
An exclusive launch receipt and fresh scratch directory prevent another launch.
The worker checks its direct parent against the saved supervisor PID.

## Saved evidence and incomplete runs

`result.json` is the worker's terminal receipt; `execution.json` records the
supervisor result, watchdog state, logs, and final cursor. If the worker is killed
before its terminal receipt, the supervisor still saves `execution.json` with
the committed cursor. Neither an incomplete run nor a fixed point implies
feasibility or an exclusion for an unprocessed case.

Every trace is a separate deterministic gzip member containing one JSON line.
The unresolved survivor stream uses the same encoding and includes the input
identity and final assignment hashes. Each completed member is flushed before
an atomic cursor replacement. On process interruption, only each file's prefix
ending at its cursor byte offset is committed evidence; any tail is retained.
The protection covers process interruption, not power-loss durability.

The cursor identifies the exact completed input prefix `[0,next_survivor_index)`
and includes outcome totals, byte offsets, forcing and row counts. A cooperative
interruption inside a case saves all its forcing steps, pass and next row; that
case stays outside the completed prefix. No automatic resume is implemented.
Full traces reconstruct selected and removed sets from the initial empty state;
final masks use the benchmark's 376-byte little-endian hash convention.

Any fully determined candidate is combined with its 20 pinned blocks and must
pass both package and standalone full-cover verifiers before being saved as a
64-block witness. Large traces, survivors, candidates, cursor and process logs
remain under ignored `experiments/scratch/`.

`check_preparation.py` exercises the three watchdog outcomes, its nonzero-exit
path, and compressed-prefix recovery with mocks and temporary data only. It does
not start a child process, signal a process, propagate a real case, or run a solver.
