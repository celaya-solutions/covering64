```
Document:    Lossless Fixed-g5 Certificate Archive
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      f4c1f63c8ca46c0ab23e99ef6b3fd5009c7d6aad3efa7822d65f67505c21264f
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Lossless fixed-g5 proof archive

XZ with LZMA preset 9 and EXTREME compresses the unchanged signed-row JSON payload from 39,902,633 bytes to 5,949,200 bytes. The original gzip archive is 8,848,020 bytes. This attempt did not meet the 5,000,000-byte target, so both binary archives stay at their frozen local paths but are excluded from Git. No proof content was rewritten or split.

The XZ archive is `all-g5-cuts.compact.json.xz`, SHA256 `9ea62be02deaf717aee1e91f86bb7b9900654490645fd31b2106670483bb2336`. It decodes byte for byte to payload SHA256 `66fbb071a8df1b33c1e2e3cb153e8c1370742d07e8e94fc2d22e8c08133719da`. Rebuilding coefficient arrays from its saved signed rows restores the full 244,012,730-byte bundle with SHA256 `cde34265aac34b735dde6a52d2c28eb190fa20b31c4f1e588193b18b387e3568`. The original gzip SHA256 `22311f1f765e46a4ffb6a92b01a54474a6e8d96056d9a511ec096340fdb43ea8` is unchanged.

The saved source `archive.py` provides `restore(payload)` for a decompressed signed-row JSON payload. The full input and output paths, lengths, hashes, settings, and round-trip receipts are in `result.json`, SHA256 `fe283b77a7220a90c5a57971fc2b3673a0d97c2f2c2428bf8398e3ab9fba0a04`. The full bundle stays under ignored scratch. This step only packages existing evidence and makes no optimization or mathematical claims.
