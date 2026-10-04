```
Document:    Declared-Partition Relabeled Core Transport
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      b6d18df95ab8d6481cc9451e85c043ad8140d1e91f83ba4b9b893cc2c64c4954
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Declared-partition core transport

The saved three-hole 64-block state contains all 60 blocks of a relabeled old core. The selected full point permutation, all 60 transported blocks and lexicographic IDs, and the complete intersection are in `witness.json`, SHA256 `38bec1ea37046d37aaed0251a214523886cfa4a5f3ccfe3f99d0f6b0a2ca73c5`. A separate checker must verify this map and transport the already-audited core cap before its new row is used.

The finite enumerator considers every bijection carrying the source core's five disjoint triples onto the declared target partition: (1,2,3), (5,6,7), (8,12,16), (9,10,11), and (13,14,15). The remaining source point maps to point 4. There are 5! assignments of source triples to target triples and 6^5 choices inside those triples, giving exactly 933,120 point maps. Each such map appears once. This is complete for that declared partition, not for all 16! point maps.

All 933,120 maps were evaluated against all 60 source blocks. The largest overlap is 60, attained by 60 maps. The witness chooses the lexicographically largest 16-label map among those maximizers. The C++ run took 0.2674129590159282 seconds and made no optimizer calls. Python separately checks that the chosen map is a permutation, regenerates all transported blocks, and recounts the intersection.

The manifest binds the exact candidate and its passed independent postcheck, original core and audited cap, both sources, and serialized input. The first arithmetic run exposed two formatting-only Ruff lines; its entire source, binary, input, logs, and outputs remain under ignored development scratch. After formatting, the run was repeated with the same binary and identical witness. The final producer source passes Ruff. No source or result was silently overwritten without preservation.

This witnessed translated core row can exclude the saved state from a model of valid 64-block covers once its independent transport audit passes. It does not prove unrestricted infeasibility or produce a covering witness.
