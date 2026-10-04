```
Document:    Fixed-g5 Whole-Link Survivor Pool Preparation
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      58c7b13fe00364597c441119ab8acddb3a0b41a3bac4e3dedb28d47e485415ae
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Fixed-g5 whole-link survivor pool

Preparation passed on 2026-10-04. No optimization has run. An independent gate must bind the frozen runner and manifest before `run --gate` is allowed.

The pool contains all 3,496 unexcluded states from the independently checked fixed-g5 whole-link screen. Every state passes the graph5 registry and all 720 graph5 planes plus 353 broad planes. None occurs in the 720-entry g5 cache. The order is replacement distance from the final g5 incumbent, then lexicographic global block IDs: distance 5 has 60 states, distance 6 has 924, and distance 7 has 2,512. Point labels stay 1-based; global IDs retain the package's zero-based lexicographic ordering.

Each LP has 1,200 ordinary variables bounded by 0 and 1, 1,390 nonnegative elastic slacks, and 697 rows. It uses GLOP, one worker, seed 2026104, and a one-second solve limit. The campaign allows at most 540 solver seconds and 630 wall seconds, with pre-call guards at 538.9 and 625 seconds. The reference elastic objective is 8.152937802508724. Execution stops at numerical residual at most 1e-7, tries exact rational-primal checks, and stops even if those checks do not recover a certificate.

The preparation archive under `experiments/scratch/g5-whole-link-pool-preparation-20261004/` saves the full ordered pool, registry inventory, unconditional rows, LP specification, and 15 frozen source files. The manifest binds 1,399 source and evidence files. Execution will save each shifted model, returned primal values and duals, timing, status, hashes, and incremental logs under `experiments/scratch/g5-whole-link-pool-20261004/`.

Frozen hashes:

- Runner: `cd9a991b8d190f215c22b6cea7d20401c3c2c91058798a4fe556f882c2e96df2`
- Manifest: `2670103860a6240939933345c4627b8136f80f38e77946c4c5b8443a6dd32ac6`
- Inventory: `7cd0b0ca44676683f8722f948e0a766b78d9ee97f94b6c69aab9256cabfffb1b`
- Ordered pool: `d313d333c4991173a6265895d216cae811e703c92813e55daf7a6fbe2df39287`
- LP specification: `fb9e3a3b2e5b9f767b5ecd8daf0f1a15c9f5617f99d9d7f4eaf5c63433070dd4`
- Graph5 family: `adfa2450b519435526830910dabfa2aa0dc5aa21e3fe08badb3fd3468382cd89`

This is a finite screen of this frozen fixed-g5 neighborhood. Numerical values, timeouts, and unsuccessful rational recovery do not exclude the unrestricted problem. An exact fractional completion would not itself be an integral covering witness or a global lower bound.
