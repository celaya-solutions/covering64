```text
Document:    Complete First-Link Linear Screen Evidence
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      66b79b4e135cc65dbfe5ae50f37844acf0c463c572574c000b752dd90695b75d
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Completed screen

All 258 first-heavy-link representatives were screened. Exactly checked row
certificates exclude 27 cycle and 73 matching cases. The remaining 102 cycle
and 56 matching cases are numerically LP-feasible and remain open. This does
not settle either the complete four-sevenfold branch or C(16,5,3).

The independent replay is in `../four-seven-link-lp-independent/`, including
`full-v1.1.0-final-audit.json` and damaged-certificate controls. Representative
completeness and all maps are checked in `../four-seven-link-orbits/`.

`summary.json` preserves every result and certificate gap, with hashes of the
full certificate and its weight vector. `artifact-manifest.json` identifies
the exact source snapshots, models, raw row arrays and full proof archive.
The full proof archive and large models remain outside Git at
`experiments/scratch/four-seven-link-lp-full/`. They must be preserved to replay
the certificates. Hashes and summaries alone are not replacement proofs.

The initial all-row-soft pilot produced no checked exclusions within its time
budgets. The second pilot and full screen kept the base rows hard and softened
only the seven fixed-block rows; all six pilot certificates were independently
checked before the full screen. Original pilot files remain in their distinct
ignored scratch directories.

The attached validation logs record the frozen dependency check, 273 passing
tests plus 10 subtests, three existing SWIG warnings, and a clean Ruff run.
No cover has been found.
