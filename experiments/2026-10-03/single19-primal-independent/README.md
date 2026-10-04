```text
Document:    Independent Sole Degree Nineteen Primal Review
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      e24c1356f9e463843f8225c3668d7363aa0c457482607527122229cedae774a2
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent readback

All 38 sole-degree-19 LP records passed this independent readback. The exact
38-ID inventory matches the separately recomputed full-link point orbits.
Each archived raw protobuf and row array matches its independent encoding
audit and hashes. All source snapshots, saved primal hashes and result records
are checked. No optimizer or model builder is called.

Every saved primal is fractional. Its binary floating-point values are converted
to one common power-of-two denominator, then every row and domain bound is
recounted with integer arithmetic. The largest exact row residual is
`26303/72057594037927936`, about `3.6502745270894366e-13`; all domain residuals
are zero. None of the 38 vectors satisfies all equations exactly as a rational
vector. They pass the stated numerical tolerance, not exact feasibility.

Nine damaged controls are rejected: truncated vector, NaN, Boolean in place
of a number, domain escape, wrong ID, changed fixed value, incorrect fractional
count, false cover claim and duplicated column index. All 38 statuses are
numerical OPTIMAL, with no extracted integer candidate or positive certificate.
No sole-degree-19 case is excluded by this screen.

# Scope and replay

The models describe the complete previously audited 38-case sole-degree-19
inventory, conditional on the separate four-class link classification and
point-orbit audit. This check does not repeat the classification or make an
unrestricted covering-number claim.

Raw archive: `../../scratch/single19-lp-v1.0.0`.
The result hash is
`89204d6e6991ffed6032aa7440d76d3c3a65cca7d1717ba66ee60b654b571e6f`.
The metadata hash is
`89ba9b4a3c062f59d0a3a60adb53fbf102b7909113238f055981c744bced5463`.
The LP runner's final summary originally hit a relative-path error after all
38 case results had been saved. The separate finalizer recovered the summary
without rerunning any solver; this readback uses the original frozen results.

Run `uv run python experiments/2026-10-03/single19-primal-independent/check.py`.
`audit.json` records exact residual fractions, every model/primal hash,
source dependencies and the damaged-control outcomes.
