```
Document:    Fixed-g5 Whole-Link Exact-Certificate Extraction Plan
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      6df849b3953b09f7241e84062ccf46e387c1a61b8e2abfaad3bb10352cf6a8d5
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Fixed-g5 exact-certificate extraction plan

Prepared on 2026-10-04 while the single gated whole-link pool sweep runs. Extraction has not run. The source SHA256 is `e40b038f8afa2542c0200b7be8fa2f101f887db0afb737cb740e982a14c749c2`.

1. Require a passed independent pool postcheck that binds the saved sweep result. Recheck the frozen runner, manifest, input hashes, graph5 family, candidate prefix, returned status, model hashes, and numerical-dual hashes. Stop if any evaluated state lacks an OPTIMAL record or if the sweep reports numerical zero.
2. Rebuild each evaluated state under the graph5 rows. Reuse the audited exact arithmetic from the g1 extraction with denominator 1,000,000, replacing all graph-specific basis, metadata, and paths with g5. Require a strictly positive exact source gap and signed row norm at most 1,000,000 for every new certificate.
3. Append the new graph5 planes to the existing 720 graph5 planes. Keep the 353 broad planes separate. Save full coefficient arrays under ignored scratch. Save signed-row compact form durably and require byte-for-byte restoration of the full bundle.
4. Hand the extraction report and compact archive to a separate checker. That checker must independently rebuild all coefficients, source shifts, exact gaps, norm bounds, hashes, and malformed controls, and verify that new source states are distinct from the prior 42,940 excluded whole-link states.

The checked whole-link neighborhood has 46,436 registry-safe states. Its prior exact screen excludes 42,940 and leaves 3,496 states. A wall or solver budget stop leaves an evaluated prefix; extraction must report the remaining count. Only 3,496 new positive certificates plus an independent union check can close this finite neighborhood. No result from this step proves a full-family exclusion, an elastic optimum, a 64-block covering witness, or an unrestricted lower bound.

Run after the independent pool postcheck passes:

```sh
uv run python experiments/2026-10-04/g5-whole-link-certificates/extract.py
```

Full output will be saved under `experiments/scratch/g5-whole-link-certificates-20261004/`; this folder will contain the report and compact archive. The extractor makes zero optimization calls.
