```
Document:    Fixed-g5 Whole-Link Sweep Outcome
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      c5244f283b40b221c843cd202495e9ce51e057b9dc4cefbe071eb6f1903ca256
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Fixed-g5 whole-link sweep outcome

The gated sweep stopped at its wall guard after 3,441 of 3,496 states on 2026-10-04. All 3,441 saved evaluations returned OPTIMAL. It used 497.4939717226662 solver seconds and 625.1666496660328 wall seconds, within the 540 and 630 second limits. No other optimizer was launched.

The minimum evaluated-pool objective was 8.47146167378511 at rank 250; the saved vector recount was 8.471461673785473. The previous best, 8.152937802508724, stayed unchanged. There was no numerical zero, exact fractional completion, or covering witness. Fifty-five pool states remain unevaluated.

The full result SHA256 is `91e0359aa2bfbc58d46da5f89ab64a682e4c4cb71902c8f0401b0db689bad8dd`. The deterministic compressed copy is `result.json.gz`, SHA256 `1e7fa5838d494de2760f963eaab1462bc7cd9b7a53290e3dcedb4b0e670f0a4f`, and restores exactly to `result.json`. The result binds 10,332 raw files under ignored scratch, including all evaluated models, primal values, duals, and logs. The runner, manifest, gate, ordered pool, and preparation files remain unchanged.

The independent result postcheck is pending. Exact-certificate extraction is prepared in the neighboring `g5-whole-link-certificates` folder and has not run. This numerical sweep makes no finite-neighborhood exclusion, full-family exclusion, elastic optimum, or unrestricted covering lower-bound claim.
