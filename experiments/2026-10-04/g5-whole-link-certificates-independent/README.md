```text
Document:    Independent Fixed G5 Whole Link Closure
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      bc3eb21fb309d3c630e1235d8a52977b9161ab970b6ba6106ec05e28004ed053
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Exact finite matching-neighborhood result

Independent replay passed for all 3,441 new signed-row certificates and all 55 unevaluated tail states. Together with the earlier 42,940 independently excluded states, this excludes all 46,436 registry-safe whole-link replacements in the declared fixed-g5 neighborhood. It does not exclude the full graph-5 family, larger changes, or unrestricted 64-block covers, and does not prove an elastic local optimum.

The checker reconstructs the 697 graph-specific rows, sums exact integer row weights over all 1,200 ordinary columns and 276 heavy columns, verifies every positive source gap, and compares the saved tail envelopes against every new plane. The minimum new source gap is 8471339/1000000; the minimum tail envelope is 6980899/1000000. Three damaged certificates were rejected. There are 4,161 graph-5 planes including the 720 prior planes; the 353 broad planes remain separate.

Compact signed-row storage was independently expanded to exactly the original 244,012,730-byte full bundle. Large raw and compressed proof archives stay outside Git; `../g5-whole-link-certificates-archive/` records the lossless archive paths, sizes, hashes and restoration. Audit SHA256: `e334b1e040959ca92be5dab37ff535f7e52ff501e356a019fb58d724b2c51716`. No optimizer ran during this replay.

Run from the repository root, with the locally preserved raw evidence present: `uv run python experiments/2026-10-04/g5-whole-link-certificates-independent/check.py`.
