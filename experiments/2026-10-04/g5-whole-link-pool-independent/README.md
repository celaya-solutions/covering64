```text
Document:    Independent Fixed G5 Whole Link Pool Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      a17ad7a776dcecf8ec8f41930ec74d78dbbb5d894f2dd295bff74b91afac3163
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Checked matching pool run

The pre-run gate independently rebuilt all 3,496 graph-5 candidate models and checked all 13,984 link receipts, ordering, source snapshots, and budget settings. The postcheck independently recounted all 3,441 evaluated vectors, reconstructed their saved 697-row models, and checked graph-specific registry receipts and raw hashes. No optimizer ran in either audit.

Every evaluated LP returned numerical OPTIMAL. The saved incumbent 8.152937802508724 did not improve. The run used 497.4939717226662 solver seconds and 625.1666496660328 wall seconds, leaving 55 candidates unevaluated under its declared guard. No numerical zero or fractional completion was found. Postcheck SHA256: `3db6431144b38c8a157512efe046a9f10f7549bd6e6a29a424af95cb759ca634`.

The independent exact certificates and tail replay are in `../g5-whole-link-certificates-independent/`. This numerical readback alone is not an exact infeasibility proof, a full-branch exclusion, or a global lower bound.
