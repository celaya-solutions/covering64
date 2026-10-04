```
Document:    Original Star Repair Audit Finding
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      403dda088e2e5b34fdc1b6540ee436cc8fd379405336700f7105b46a834a4b74
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Preserved original finding

The original prepared star-repair package was not launched. Its vector checker
accepted non-integer numeric values because it tested only whether each value
lay inside a variable's domain intervals. Both float-valued and boolean-valued
copies of the valid hint passed. More seriously, changing uncovered indicator
variable 4404 from one to 0.5 passed all its checks: the truthy value activated
the zero-coverage row and skipped the opposite enforcement, while satisfying
the numeric interval and hole-budget checks.

`original-findings.json` binds the original source, manifest, and model bytes,
plus the concrete single-value mutation. No solver was launched. The original
producer folder remains unchanged. The corrected v2 sibling adds an exact
integer-type check before domain evaluation and receives its own independent
gate; this original package receives no GO.
