```text
Document:    Independent Matching Graph Five Link Descent Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      c958df9e2a052c1b1b26e29b84993129792ddabc07bf031836b41bb075f48a57
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

The gate independently reconstructs the 697-row matching graph-5 model with
hub-pair targets 7,5,5,5,5,7. Its initial 127 structural two-edge neighbors have
86 registry-admissible and 41 rejected states. Both transports for all four
anchor-link classifications are checked against the audited registry. The
only initial cache entries are the two separately checked graph-5 diagnostics;
their primal, dual, tuple, row and family hashes are rebound. Duplicate and
damaged-map controls are rejected.

The postcheck replays three complete neighborhoods: 127,128,128 generated
states; 86,86,84 accepted; and 41,42,44 registry-rejected. All 256 evaluated
records report OPTIMAL, comprising 253 fresh LP calls and three cache uses.
Every shifted row set, saved numerical vector, registry receipt and cache
origin is checked, including the final cache and selected trajectory.

The numerical objective falls from 15.06922063054413 to 13.221637797152143,
then 12.594498845064832, then 11.500690015970484. The run uses
33.94579962082207 solver seconds and 38.15049670799635 wall seconds. It stops
at its three-round limit while still improving, so it does not establish a
local minimum. It supplies no global bound or covering witness.

This branch uses its own matching model and cache. The graph-1-only planes and
cache are not reused. The independent scripts invoke no optimizer. Ruff passes.
