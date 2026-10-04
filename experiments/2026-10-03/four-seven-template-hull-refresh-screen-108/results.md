```text
Document:    Results of the 108-Version Matching Template-Hull Screen
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      14036a8ddb309d34612bee2690d7e3826e9fa516774a81fff792f4e2ff4f3f05
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# 108-version matching screen results

The whole matching branch and all 48 remaining matching first-link types
returned numerical OPTIMAL. There were no new positive certificates, no
unknowns or timeouts, and no near-integral block candidates. This completes
the requested LP-pruning iteration with **108 checked exclusions and 150 open
first-link types**: 102 cycle and 48 matching.

The 108-version catalog has 12,042 templates per heavy group and 52,936 matching
variables. It removes 648 templates per group from the 106 version, whose
sources, data and integer pilots remain unchanged. Cycle files are byte-identical
and were not rescreened.

The 49-case run used 210.393474 solver seconds. Its longest case used
10.598079 seconds, below the 15-second per-case ceiling. Root independently
audited the complete new catalog, transports and matrix, including 16 damaged
controls. The new no-solve preflight checked four layouts, all 96 fixed/reset
transitions and 46 damaged controls. Final readback passed all 49 records and
49 sparse primals, rejecting six damaged controls. Exact arithmetic on the
stored binary values found a largest numerical row residual of about
`4.3831e-12`. The primals have 394–462 fractional block values.

This is a stopping point for the specified numerical LP-pruning procedure.
It does not prove exact LP feasibility, produce a covering witness, close the
regular branch, or establish an unrestricted lower bound. No further catalog
pruning is justified by this wave because it generated no new checked
exclusions. Other independently audited integer/proof methods remain separate.

## Frozen evidence

- Raw output: `experiments/scratch/four-seven-template-hull-refresh-screen-108-20261003/`.
- Results SHA-256: `bbaf574354d53c7e8a8889261a6200b46d1b5a06b697379c9e79de8a43bce87d`.
- Readback audit SHA-256: `fd1f5886b52271efc9fd27e2ee642edae3575aa4bc6bc4c6d0dac6a4d027ed1a`.
- Preflight SHA-256: `3dfff17a52b94568c1b3e5acce5fc61ee92ab5202420d89e50db5ac8ccdf73a3`.
- Catalog manifest SHA-256: `dcbdfd83d9c1952fbcbc0e2e192897ce96fae126aa0d527011ca6f0e13eb8c87`.
- Matrix SHA-256: `e9b2289291479c5f1119f432f0131d8fda8130ace2e64c773cf93dd8928ceade`.

The machine-readable summary lists all 48 remaining matching IDs and records
the stopping reason. Individual results retain complete row identities,
solver logs, timings, state audits, sparse primals and frozen source provenance.
All earlier versions remain available unchanged.
