```text
Document:    Independent Registry Filtered Graph One Descent Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      06233f8039645ae56f41a8197aabcdeafcdfe6bc20b10979f80b880b23adcfca
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

The gate independently reconstructs the 697-row fixed-graph completion model.
Only six hub-pair bounds change from the broad model: row indices
622,626,630,664,668,690 have exact targets 5,6,6,6,6,5. Labels remain 1-based and
global block IDs retain zero-based lexicographic ordering. The branch baseline
is 8.024244815488677, separately measured from the broad-model objective.

The independent endpoint-degree enumeration finds 136 two-edge neighbors.
For every state it checks the tuple, all shifted rows, 14 exact cut rankings,
and each of four first-link orbit receipts against the audited 109-exclusion
registry. Both valid point transports are checked. The registry admits 122
neighbors and rejects 14. The initial cache contains only the fixed-graph
baseline; profile keys include the exact family, heavy tuple and row hashes.
A duplicate-neighbor control and a damaged point-map control are rejected.

The postchecker replays both complete neighborhoods and the entire cache.
Each round has 136 generated, 122 accepted and 14 rejected states. All 244
evaluations report OPTIMAL; 243 are fresh and one reuses the baseline. All
saved primal and dual hashes, 1,200-entry ordinary vectors, registry receipts,
shifted rows, ranking files, cached origins and final cache are checked. The
run used 31.963778204168193 solver seconds and 35.75381783291232 wall seconds.

The first round improves the numerical objective to 7.52051548546158. The
second round's smallest independently recounted residual is 7.978655120128568,
so the run stops after a complete accepted neighborhood without improvement.
This is numerical local-minimum evidence within the fixed graph-1,
registry-filtered two-edge neighborhood. It proves no global optimum or
unrestricted lower bound and supplies no covering witness.

The audit scripts invoke no optimizer. Ruff passes. The gate and postcheck
receipts bind their final source versions and all input evidence.
