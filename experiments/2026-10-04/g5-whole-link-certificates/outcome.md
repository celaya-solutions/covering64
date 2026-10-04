```
Document:    Exact Fixed-g5 Whole-Link Source-Certificate Outcome
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      30f25407560e0496e7472290d37274e1ed8e5d3c0ea5a54d3deb034aa9e321db
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Exact source-certificate extraction outcome

The solver-free extractor ran once after the independent pool postcheck passed. It derived 3,441 strictly positive source certificates at denominator 1,000,000. The minimum exact source gap is 8,471,339 / 1,000,000, from pool rank 250. With the 720 prior graph5 planes, the bundle contains 4,161 distinct graph5 planes; the 353 broad planes remain separate.

The full bundle is preserved under ignored scratch: `experiments/scratch/g5-whole-link-certificates-20261004/all-g5-cuts.json`, 244,012,730 bytes, SHA256 `cde34265aac34b735dde6a52d2c28eb190fa20b31c4f1e588193b18b387e3568`. The durable `all-g5-cuts.compact.json.gz` is 8,848,020 bytes, SHA256 `22311f1f765e46a4ffb6a92b01a54474a6e8d96056d9a511ec096340fdb43ea8`. Its restoration was checked byte for byte against the full bundle.

The extraction result SHA256 is `1ee19f72b69e551bc655bce554cf55fb431bd94dad9bf2f0a11162bae046c81f`. The source and frozen input chain bind the g5 rows, saved numerical duals, model hashes, passed pool postcheck, prior exact screen, and compact restore source. This extraction made zero optimization calls.

The neighboring tail screen subsequently evaluates the 55 states left by the sweep's time limit. Exact source arithmetic and tail coverage await independent replay. No full-family exclusion, elastic optimum, covering witness, or unrestricted lower bound is claimed.
