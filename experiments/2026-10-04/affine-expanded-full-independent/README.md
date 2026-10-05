```text
Document:    Independent Gate for Full New-Only Affine Support
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      69615a1d2246a71b8e1f75430faf02730481ef8455b79e28633f014acd0354b8
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Review scope

This gate reviews the corrected additive v1.0.1 full support runner. It does not
launch a production pass, call the real support screen, or run an optimizer.
It relies on the accepted independent catalog and 1,000-case certificate audit
for the underlying arithmetic. It imports the producer only to check input
loading, identities, partial-mask construction and mocked execution controls.

The checker independently enumerates the complete new-only identity order from
the 38 fiber records and mapped old IDs. It compares every one of the 6,543,904
new identities, confirms all 195,296 old pairs are skipped, and preserves the
original 6,739,200-pair ordinal space. The ordered identity digest encodes four
little-endian unsigned 32-bit integers per case: fiber, partial, profile, ordinal.

It reconstructs all 4,368 global pentads, all 3,003 point-avoiding columns, all
455 exact row-support masks, all 1,300 profile masks, and 114 sampled partial
masks spanning every fiber. It verifies that the imported arithmetic functions
have unchanged code, with only the documented total-pair constant changed.

Synthetic controls exercise complete batches, interrupted case/survivor/ledger
writes, failures before and after atomic cursor replacement, damaged cursor
fields and hashes, uncommitted tails, invalid batch order and forbidden resume.
An independent prefix verifier checks gzip members, ledger entries, hashes,
identities, outcome counts, byte boundaries and cursor indices together.

Mocked processing loops cover a complete six-case run, stopping at 649 seconds,
loading timeout, and an error leaving an evaluated but uncommitted record.
Mocked launchers cover success, nonzero exit, TERM, KILL, and child-exit races
before both group signals. No child process or real process signal is created.
Damaged gate fields and deadline controls are rejected.

The original v1.0.0 launcher lost its final receipt when a mocked child-exit race
raised ProcessLookupError during group signaling. Its producer remains unchanged.
The additive v1.0.1 catches that race and still waits, reaps, and saves the receipt.

The authoritative durable state is the on-disk cursor. Bytes beyond its saved
case, survivor and ledger offsets are uncommitted tails. If a failure occurs
after cursor replacement but before the writer updates its in-memory cursor,
the on-disk cursor still identifies the valid committed prefix.

Only the exact producer, launcher and manifest hashes named by `gate.json` are
approved. The shared 650-second cooperative scope includes launcher validation,
loading, processing and output; new cases stop at 649 seconds. The external
watchdog is 660 seconds with 5 seconds of termination grace. There is no retry
or automatic resume. A GO authorizes root to run this bounded conditional
screen; it proves no global covering-design existence or nonexistence claim.
