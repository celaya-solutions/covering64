~~~text
Document:    Gated Full New-Only Affine Support Runner
Version:     v1.0.1
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      ee5ecf4db20cdf07e86fc2f94e26dd83f22b613636882ffb90152e47a8d8f1c4
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
~~~

# Prepared, not launched

This additive runner is prepared for root's later decision after the
independent GO gate. Preparation did not screen any additional pair or run an
optimizer. It would make one support pass over the 6,543,904 new compatible
profile/link pairs in the expanded four-class affine recipe. Its source has no
resume mode or automatic retry.

The root-accepted catalog and 1,000-case audit is pinned at
`../affine-expanded-independent/audit.json`, SHA256
`66f1cf20c56a7099979ac1184862e9ac1db8f50f1646704121cdd314b00ab5bc`.
The separate runner gate belongs at
`../affine-expanded-full-independent/gate.json`. Both the launcher and child
require `decision: GO` and exact runner, launcher, and manifest hashes. The gate
does not itself launch the work.

# Domain and order

The original frozen `screen`, `locate`, and `global_ids` functions from
`../circulant-chosen-link-support-screen/run.py` are imported unchanged. Only
the module's `TOTAL` constant changes, from 195,296 to 6,739,200. The manifest
lists that override and no others. The mathematics remains all 3,003
five-subsets avoiding point 1, all 455 residual triple equations, and exactly
44 selected blocks. The loader verifies all 66 carriers of each triple.

The full ordinal order is fiber, partial ID, then profile ID. The new-only
order is that same order with precisely the 5,536 mapped old partial IDs
skipped for every associated profile. Those skips remove exactly 195,296 old
pairs. The loader compares all old twenty-block families against their mapped
packed records and verifies the skip-set partition across the 38 fibers.

Each output record preserves its original `pair_ordinal`, `partial_id`, and
`profile_id`, plus `excess_link_id` and a consecutive `new_pair_index` from zero
through 6,543,903. `locate_new` converts that consecutive index to the unchanged
full domain. The core's returned IDs must agree with the new-only mapping.

The loader reads the packed catalog and all profile/carrier masks. It then
constructs one partial's eighty-row mask at a time and reuses that mask for
all profiles associated with the partial. It does not retain all 196,992
partial masks in memory.

# Time limits and launch boundary

Root's explicit launch command, after independent GO, is:

`uv run python experiments/2026-10-04/affine-expanded-full-support-v1.0.1/launch.py root-authorized-run`

The launcher begins a shared monotonic clock before its gate/source validation
and passes that clock to the child. The child's 650-second cooperative scope
therefore includes launcher validation, source and catalog loading, processing,
and output. It stops starting cases at 649 seconds, checks again after preparing
a partial, then flushes its pending batch and writes its receipt. It reports
any overrun instead of claiming completion within budget. Cooperative checks
occur between operations; a blocked system call is not a hard deadline.

The external watchdog waits at most 660 seconds from the shared clock. If the
child is still running, it sends SIGTERM to the child's process group, allows
five seconds for termination, then sends SIGKILL if needed. The child handles
SIGTERM by stopping at the next case boundary and attempting to commit pending
records. The launcher does not restart a stopped process. It records the whole
child duration, including its receipt, separately from the child timing.

The launcher rejects any prior launch directory, raw output directory, result,
or launch receipt. The child also rejects prior raw output or result files.
An incomplete pass requires a separately reviewed decision; no file deletion,
automatic resumption, or hidden retry is part of this runner.

# Durable evidence and authoritative cursor

Large output belongs only under ignored scratch paths:

`experiments/scratch/affine-expanded-full-support-v1.0.0/`

`experiments/scratch/affine-expanded-full-launch-v1.0.0/`

The support directory contains `cases.jsonl.gz`, `survivors.jsonl.gz`,
`commits.jsonl`, and `cursor.json`. Every batch of at most 1,000 cases is written
as one complete gzip member per stream. An empty survivor batch still writes
a valid empty gzip member. The gzip level is six and the member timestamps are
zero. Concatenating the committed members is a valid gzip stream.

For each batch, the writer performs these steps in order:

1. Write and fsync both complete gzip members.
2. Write and fsync one ledger entry with byte boundaries, member hashes,
   uncompressed hashes, new-index range, full ordinal endpoints, and counts.
3. Write and fsync a temporary cursor, replace the prior cursor atomically,
   and fsync the containing directory.

The cursor is authoritative. It records the committed case and batch counts,
cumulative outcome/operation counts, the next consecutive new index and its
full pair ordinal, and exact byte lengths and SHA256 hashes for all three
committed stream prefixes. It also pins the manifest and source hashes.

If a process stops during a batch, any bytes or ledger entries beyond those
cursor lengths are uncommitted. A consumer must use and verify the cursor's
prefixes, rather than treating full file lengths or a longer ledger tail as
completed evidence. The cursor is also authoritative if a final summary is
missing or stale. At full completion it has 6,543,904 committed cases, next
new index 6,543,904, and a null next full ordinal.

`result.json` and `launch-result.json`, created only by a later launch, are
small receipts suitable for tracking. The former records committed versus
evaluated cases and the shared budget status. The latter records the external
watchdog result, log hashes, whole-child timing, and saved cursor. Exclusion
certificates and survivor records remain in the gzip streams.

# Frozen pins and planning limits

Runner SHA256:
`82519beeb3de034fab824945e10e40850bf87bfe50883ea93e8a4b7168a24f63`.
Launcher SHA256:
`f7c140d858654045d89dc0077360f654cd347adf5c1db2d6bf1e01e238a1163a`.
Manifest SHA256:
`53056e681503426c9f80b4c7a1aba1627408f5a439c75b4738b832b2ad63ac81`.

The preceding sparse benchmark estimated about 525 seconds and 518 MB of
compressed certificate output for the new pairs. This is a planning estimate,
not a bound. The new batch commits and fsync calls add overhead that the earlier
single-stream benchmark did not measure. The 650-second budget may therefore
end with a valid partial prefix. Neither an exclusion here nor a complete
recipe pass would rule out covers outside the stated affine recipe and
circulant excess-profile scope.

The additive v1.0.1 launcher catches a child-exit race before either group signal.
A missing process is still reaped and its launch receipt is saved. The original
frozen v1.0.0 source and manifest remain in their sibling folder for provenance.
