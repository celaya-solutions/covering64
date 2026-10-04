```text
Document:    Independent H12 Soft-Pair Preparation Gate
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      7cfecc62431bfcdcbe1a8864998c31a73e76bf02e929e0a383b65106b101b58b
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Gate result

The independent gate passed without calling an optimizer. It binds the existing soft-pair model and checks that replacing the solution hint is the only proto change. The parameters differ only by 120 to 300 seconds and seed 2026104302 to 2026104901; four workers remain unchanged.

The H12 witness is independently recounted into all 5,728 values. All 14,405 rows and domains accept that complete hint: 12 holes, actual maximum-per-pair and full-row deficits both 34, and objective 19,086. The four named core overlaps are [1,1,1,2]. Decreasing a required deficit fails; increasing it as auxiliary slack remains valid.

The runner's entire Python syntax tree equals the prior reviewed runner after changing the output directory and extending frozen hash validation to include the new input receipts. Saving complete vectors, independent covering checks, actual-versus-auxiliary deficits, and the actual-zero stopping condition are unchanged. The gate binds the old runner, row checker, model, parameters and new source inputs by their hashes.

This authorizes one root-owned run using the frozen model. An actual-zero deficit with positive holes is a qualified partial hint, not a cover. No global lower bound follows from a timeout or failed construction.
