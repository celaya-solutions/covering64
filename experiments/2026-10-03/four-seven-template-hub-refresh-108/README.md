```
Document:    Targeted Refreshed Hull Hub LP Results
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      52a2e7816c61015a8140c33d70590de6f715a6aab0fc364e06d0f13c37d8444d
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Result

Both remaining hub cases returned numerical OPTIMAL on the refreshed 108-exclusion template hull: matching-029 at (m4,z)=(0,2) in 4.918858 seconds, and matching-063 at (0,1) in 4.392581 seconds. Each had a 15-second solver budget. Neither produced an integral candidate or a certificate. The checked first-link exclusion union stays at 108; 150 representatives remain open.

Each model has 52,936 variables and 4,559 rows: the audited refreshed 4,550-row matching hull, the two exact hub equations, and seven fixed-block equalities. The nine added equalities are byte-for-byte equal as row lists to those independently audited for the separate 106-catalog CP pilots, reordered to keep the frozen hub runner layout. Only case selection and equalities are borrowed from those pilots; the LP matrix is the audited 108-catalog matrix e9b2289291479c5f1119f432f0131d8fda8130ace2e64c773cf93dd8928ceade.

Four feasibility/phase-I layouts were fully compared against frozen row lists and domains before their respective solves. Sixteen changed-row controls were rejected. No phase-I solve was needed. Independent numerical readback reconstructed all 4,559 rows per case, checked both saved primals, bound source/log hashes, and rejected eight damaged primals. Its largest exact-binary row residual was below 8e-13. The first 4,368 block coordinates contained 396 and 399 fractional values.

These floating-point outcomes do not establish exact LP feasibility, integer feasibility, nonexistence, or a global lower bound. No candidate was sent to cover verification because neither result was near integral. Exact certificate construction remains available in the runner but was not invoked after numerical OPTIMAL.

Raw matrices, solver protos, primals, metadata, frozen sources and solver logs remain outside Git under experiments/scratch/four-seven-template-hub-refresh-108-20261003. summary.json binds the saved hashes. The runner source, readback checker and compact results are retained here. Targeted Ruff passed. Root owns the full project checks and commit.
