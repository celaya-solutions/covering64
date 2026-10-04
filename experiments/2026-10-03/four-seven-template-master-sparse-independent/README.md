```text
Document:    Independent Sparse Heavy Master Truncation Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      6c9c21078c7ef5a00f28fb323a0434c23e0f7373d2b9fb2be612034bd9dab00b
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent sparse-master gate

The sparse model passed. It contains exactly the first4,768 variables and first4,270 rows of the previously audited master. Every retained row refers only to retained variables. The independently reconstructed276 heavy-block columns remain integer; ordinary blocks and double variables remain continuous. Restoring the deleted50,760 template variables and280 hull rows reproduces the entire source protobuf exactly. No other field changed.

Eight damaged integrality, row, bound, objective and name controls were rejected. A fresh SCIP instance loaded and re-exported the sparse model identically and accepted one thread. This checker did not call Solve. `audit.json` is the machine-readable gate; `check.py` and `audit.log` preserve the check.

This is a strict seed relaxation with template membership constraints removed. A feasible heavy pattern must pass membership in the current108 catalogs before native search or integer completion. Fractional ordinary blocks are not a covering witness. This gate proves neither feasibility nor infeasibility of the covering problem. Full-file hashes are in `manifest.json`; the header hashes only this body.
