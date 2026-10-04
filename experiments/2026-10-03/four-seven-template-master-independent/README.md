```text
Document:    Independent Heavy Template Master Relaxation Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      255a9d5783402a48124948e621ac151f6c882826f3400b0d00bef85b6da017a7
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent master relaxation audit

The model passed. This checker independently enumerates the 4,368 lexicographic five-blocks and reconstructs 69 possible heavy-block columns for each of four anchor groups. The 276 columns are disjoint. The master retains exactly these integer variables and changes exactly 4,492 original Boolean flags to continuous. Restoring those flags makes the entire MPModelProto equal to the previously audited source, including every row, bound, coefficient, objective, name and column order. The 50,760 template weights were already continuous. All eight damaged integrality/row/bound/objective/name controls were rejected. No solver was called by this audit.

The master has 55,528 variables and 4,550 rows. It comes from the older 106-catalog matching MIP. Ordinary block and double variables may be fractional, so a feasible result is a heuristic heavy-pattern seed only. It is neither a covering witness nor an exclusion. The proposed runner checks finite values, bounds, numerical row residuals and heavy integrality, then extracts exactly 28 heavy blocks as seven catalog edges per group. Any later transfer to the native search must also pass membership in the newer 108 catalogs, followed by native seed and covering checks.

`audit.json` is the model gate and `check.py` is the independent checker. Raw source and relaxed protobufs remain in ignored scratch archives. The full-file hashes in `manifest.json` bind the evidence; the header SHA256 hashes this body.
