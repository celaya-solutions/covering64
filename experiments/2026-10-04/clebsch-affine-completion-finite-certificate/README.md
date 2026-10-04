```text
Document:    Finite Certificates for Seven Fixed Affine Link Completions
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      9ea8a45faa86bc08c578d1004d6a035b25510ab467c68938e261b878ed7ea0d6
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Seven exact partials

These certificates concern the seven pinned twenty-block partials and their
pinned triple-excess profiles from the completion pilot. They do not exclude
all local links, all embeddings, any complete excess profile, or general covers.
The other 249 selected partials have separate earlier finite certificates.

For each fixed point, all 3,003 avoiding pentads remain in the initial domain.
The twenty fixed blocks are subtracted from each of the 560 lexicographic
triple demands. The residual demand is exact, and 44 further pentads are
required. Row bounds propagate fixed values. When setting an unassigned
variable to one yields a row contradiction, its value zero is forced in the
parent state. Every force and failed-literal branch is retained for replay.

The producer closes all seven cases with respectively 5, 8, 4, 6, 7, 4 and 10
failed literals in 0.112799416994676 seconds, under a twenty-second finite budget.
No optimizer is called. Rows use the original global block IDs; they are not
renumbered after deleting the fixed point. The saved certificate hash is
`935783a788c93d79046bf9599af2d95735e5ce087a43c876a6516acfbcfc7841`.
The independent bitset replay checked all seven contradictions, 44 failed
positive literals and 1,069 force steps, and rejected 43 damaged controls.
Its audit SHA256 is
`24c9d8ff0cc3db79ed95a46493c5ffd7e6d662e1b54e1e8f8df6e3997a510b8e`.
Together with the earlier checked 249 exclusions, this closes the 256 saved
partials only; alternate local constructions and label maps remain open.
The earlier seven CP-SAT statuses remain distinct from these finite deductions.
