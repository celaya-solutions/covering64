```
Document:    Exact Fixed-g5 Unevaluated Whole-Link Tail Screen
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      8ac1315435fa67634051ba49f604c3e8ab2fcd25f6f228ba2536b2505b03efda
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Exact unevaluated-tail screen

This separate frozen screen uses integer arithmetic on the 3,441 newly extracted graph5 planes. It evaluates exactly the 55 states after the saved 3,441-state pool prefix, with no optimizer calls. All 55 have strictly positive gaps. The minimum is 6,980,899 / 1,000,000 at pool rank 3472, using plane `g5-whole-link-rank1161`.

The script binds its source, extraction result, full and compact certificate bundles, passed pool postcheck, pool manifest, ordered pool, registry inventory, and prior exact screen before running. It performs 189,255 new-plane/state evaluations, saves every tail state, best supporting plane, exact bound, and registry receipt in `scores.json`, and saves the empty remaining set in `unexcluded.json`.

Frozen hashes:

- Source: `a4f59fdb163afe8b1e8c26f8c26c77d9d62f10e06507b97b0de508bd89501163`
- Manifest: `24aeb61dd2b1942532822f9f9f5825567ff70b00cf18a3b6090606efd08f0772`
- Result: `bdd599aeec8381c22f938ae6eef0220f272d81ef5b8be6a525bda30c13291e46`
- Scores: `f054436526cffc6e4ef5781b2f81d9799f763e92e53e7ed0c3d60f383149910b`

The candidate union is 42,940 prior positive states, 3,441 new positive source states, and 55 positive tail states, totaling the 46,436 registry-safe states in the fixed-g5 whole-link neighborhood. Independent coefficient reconstruction, certificate replay, malformed controls, and the finite union check are still required. The result explicitly marks independent closure false and the finite-neighborhood result pending replay. No full-family exclusion, elastic optimum, or unrestricted covering bound is claimed.
