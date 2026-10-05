```
Document:    One Bounded Full Pass over Chosen Circulant Point Links
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      8a39db52a5165b0168f77db24444c46aa3fe5c8069174d24a1647f5014307a55
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

This sibling runner reuses the frozen benchmark's exact case arithmetic
without changing its source, manifest, or records. Root reviews the frozen
full-run source and manifest before launching. Preparation performs no case
screening. The full run is one ordered pass over exactly 195296 compatible
(profile, partial) pairs, with a 45-second wall budget including input loads
and output. It stops starting new cases at 44.5 seconds, leaving time to close
the files and save the receipt. Actual wall-budget compliance is reported.

Each case starts with all 3003 pentads avoiding point 1, reconstructs all
455 outside-point exact triple demands plus cardinality 44, removes blocks
touching zero rows, and checks support and immediate forced conflicts. It
does not fix the forced blocks and repeat. There is no optimizer, iterative
propagation, retry, or automatic resume.

The output contains one explicit certificate record per completed pair in
ordinal order. Every deficient row records its demand and all supporting
block IDs; each forced conflict records the conflicting row and all tight
rows forcing the cited blocks. Survivor IDs are also saved separately.
Both compressed files live in ignored scratch and are hashed in the result.
If capped, the result gives a half-open completed interval [0,cursor) and
the exact next ordinal. Completeness is true only when all 195296 cases
were processed. An exclusive launch file prevents accidental reruns.

Preparation command:

`uv run python experiments/2026-10-04/circulant-chosen-link-support-full/run.py prepare`

Root's launch command, after independent review:

`uv run python experiments/2026-10-04/circulant-chosen-link-support-full/run.py run`

All source and input files, including the bounded 1000-case benchmark and
the exact catalog, are pinned by the new manifest. No frozen benchmark file
is modified. The scope is all excess-graph isomorphism images of the four
chosen canonical twenty-K4 witnesses across the supplied 1300 profiles.
It remains a restricted construction catalog, not all affine constructions
or local links. A surviving pair has not been shown feasible.
