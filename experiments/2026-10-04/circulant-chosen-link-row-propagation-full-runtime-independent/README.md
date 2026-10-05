```text
Document:    Independent Full Row Propagation Runtime Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      bef50209bb3f492318ca44198c12128c73188707f2e4af5f83cb5a22462eb4ae
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent full runtime audit

The saved-only audit passed for all 10,228 completed cases. The independent
set-based checker replayed all 808,987 forcing steps and verified 9,132 exact
profile/partial contradictions plus 1,096 row-bound fixed points. It also checked
all 8,726,124 row visits and pass counts against the saved force order. No full
cover candidate, interrupted case, watchdog event, or uncommitted tail exists.

The worker reported 16.369391459040344 seconds; the supervisor reported
16.39961666695308 seconds. The worker's 45-second cooperative budget was
respected. The process exited with code zero and empty stderr, and stdout agrees
with the complete terminal summary.

## Evidence checked

The checker binds the frozen runner, manifest, all 22 manifest dependencies,
independent launch gate, independent benchmark checker and audit, root launch
receipt, terminal result, and supervisor execution receipt. It reconstructs the
195,296-case catalog order, binds all 10,228 survivor inputs to their original
profile/partial identities, and verifies the exact order of every committed
trace. Every resulting survivor record agrees with the replayed state.

Only cursor-committed gzip prefixes were replayed. Their lengths are 69,863,668
trace bytes and 238,894 survivor bytes. Both equal their complete file sizes;
there are zero uncommitted bytes in this run. Streaming gzip parsing checked
all complete member footers, and saved raw file hashes agree with the worker
and supervisor receipts. The cursor, complete prefix, outcome totals, force
counts, row visits, output counts, and empty candidate list all agree.

The independent engine is the pinned set-based checker used for the benchmark.
Its pure context and check functions were imported without running its main
entry point or rewriting its earlier receipt. No producer code was imported,
no producer was rerun, and no optimizer was called. The new audit handles saved
interrupted traces and full-cover candidates separately; a candidate would have
to satisfy all exact rows and pass both package and standalone verifiers.

Eleven damaged controls were rejected: flipped forced values, omitted literals,
wrong rows, Boolean values, altered final demands, changed state hashes, an
omitted survivor step, incorrect input position or profile identity, and wrong
pass or row-visit counts. Ruff and all document header hashes pass.

## Meaning and scope

These are independently checked finite exclusions of the 9,132 exact saved
profile/partial completion cases. The 1,096 remaining cases reached row-bound
fixed points; that does not prove they are feasible. The pass concerns only the
chosen four-witness image catalog. It does not cover all affine constructions,
all local links, all pair graphs, or the unrestricted C(16,5,3) problem.

## Reproduction

```sh
uv run python experiments/2026-10-04/circulant-chosen-link-row-propagation-full-runtime-independent/check.py --result-sha256 05a05fb907ad2b5e425977939e04ddb5c599abfa6dc9c4c203da2f9b76de6db2 --execution-sha256 4224cadcd489d985e7737933ba14854b7c4c77e183b621023ce7a9372f12872c
uv run ruff check experiments/2026-10-04/circulant-chosen-link-row-propagation-full-runtime-independent
```

The independent review SHA256 is
`aceba1e0c1280be6154950dfe61e5545ff40035cb5307e3749b1ac97c630f92a`.
The full saved evidence index is `raw-files.json`; the small tracked audit files
are bound by `files.json`. Large compressed traces remain outside Git.
