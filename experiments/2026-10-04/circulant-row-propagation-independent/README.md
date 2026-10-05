```text
Document:    Independent Replay of the Circulant Row Propagation Benchmark
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      9aa0f73de7d613c510c5f1ba7341b38ea90a2718e6def73378acab24608bc335
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Saved deductions checked with sets

The independent checker reconstructs all 456 exact rows over the 3,003
point-one-avoiding block variables. For each triple it enumerates its 66
completing pairs directly. It derives residual demands from the actual saved
twenty-block partial and the exact excess profile, without producer imports.

Every recorded zero or one assignment is checked against the current row's
selected and unassigned variable sets. The assigned set must equal the whole
currently free row support, and the relevant exact bound must be tight.
Every final contradiction is recounted; every surviving state satisfies every
row and has no remaining row-bound force. All state hashes and selected IDs
are checked. Ordinals, partial/profile identities and stratified sample indices
are reconstructed from the complete original catalog and survivor stream.

All 1,000 saved cases pass: 893 contradictions, 107 quiescent survivors and
79,165 forcing steps. Seven damaged traces are rejected. No new propagation
search or optimizer is run. This establishes the saved benchmark deductions
only; it does not establish a conclusion for all 10,228 input survivors.

The benchmark audit SHA256 is
`dcd303e56b7474a6155ac644603c3b3baa55adb0b2936ba624848d826510360a`.
