```text
Document:    Independent Double-Hub Dual Replay
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      ef578645016f3b75ee28b12c2d096198638f7507564a09e959d3cd971b910a40
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent double-hub dual replay

The standalone standard-library checker reconstructed all 4,368 five-subsets and 560 triples. It checked all 270 exact rational certificates against the bound seed archive, including ordered distinct block IDs, block labels, every missing triple, nonnegative weights, every possible block load, the reported lower bound, and the exclusion flag. All 14 damaged controls were rejected.

Four fixed 32-block families need more than 32 additional blocks:

| Family | Exact lower bound |
|---|---:|
| shape-1-class-006 | 16038801/500000 |
| shape-4-class-075 | 4010809/125000 |
| shape-44-class-000 | 32050669/1000000 |
| shape-47-class-000 | 3229623/100000 |

These exclude any 64-block cover retaining the specified 32 blocks, even if added blocks contain the two anchors. Each positive weight belongs to a currently missing triple, and every possible new block has weight at most one. Thus at least the sum of the weights is needed in added blocks.

This is a local result about these fixed families. It does not establish a global lower bound for C(16,5,3). Other certificates below or equal to 32 do not prove that a completion exists.

Run from the repository root:

```sh
python3 -I scripts/check_double_hub_duals.py \
  experiments/2026-10-03/double-hub-dual-audit/candidates.json.gz \
  experiments/2026-10-03/double-hub-dual-audit/certificates.json.gz \
  /tmp/double-hub-dual-replay.json
```

The frozen checker is also saved as `check.py` beside the two inputs and `result.json`. The result binds all three sources by SHA256.
