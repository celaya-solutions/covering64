```
Document:    Gated Global Five-Heavy DP Runner Preparation
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      30118e271b9f0ca7307f920fa3f6b08e8375a8abf5c240ac5f7396fb630be394
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Prepared execution runner

`execute.py` is prepared and has not been launched. Its read-only preflight parses the exact saved model and parameters and checks their hashes after serialization. The native parameter formatter omits the standard protobuf text's terminal newline; restoring that single newline preserves the exact frozen parameter bytes. No parameter value is changed.

A run requires a passed independent gate binding `manifest_sha256`, `source_sha256` for the preparation source, `runner_source_sha256`, `model_sha256`, and `parameters_sha256`. The runner checks every preparation input hash and refuses any existing runtime directory, candidate output directory, or result file. It loads the frozen model without rebuilding it and performs exactly one solve at 120 seconds, four workers, seed 2026104104.

The runtime snapshots the source, gate, manifest, model, and parameters. It saves incremental stdout, native solver logs, the complete native response, every composite-objective improvement, distinct callback ties, and the final native state even when it ties a callback but differs in block IDs. Every saved state includes all 10,488 variable values, direct coverage/core recounts, and an exact fixed-weight DP recount. A zero-hole callback stops the run, and zero-hole witnesses must pass both covering verifiers. Near-cover records remain subject to the separate postcheck.

The runner makes no unrestricted infeasibility claim. UNKNOWN and timeouts remain inconclusive, and native INFEASIBLE is not an independently checked theorem. The readback receipt records zero optimization calls and confirms all runtime outputs are absent.
