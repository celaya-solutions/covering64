```text
Document:    Refreshed Matching-Only Template-Hull Screen Results
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      3edab5b97fc9d12f26f00f349367f2176251d557634f8f293af69596351bc664
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Refreshed matching screen results

The whole matching branch and all 50 remaining first-link cases finished.
The whole branch returned numerical OPTIMAL in 3.659222 seconds.
Of the 50 first links, 48 returned numerical OPTIMAL and two produced positive
certificates that passed independent exact replay. There were no timeouts or
unknowns, and no near-integral block candidates.

| Independently excluded first link | Positive exact gap |
| --- | ---: |
| `matching-095` | `22563/1000000` |
| `matching-113` | `44/15625` |

Each independent replay checked the seven fixed rows, all 4,557 resulting rows,
and all 55,528 unit-box variables. Eight damaged controls were rejected per
certificate. The base matrix hash matches the independently audited refreshed
catalog/matrix exactly. These are first-link exclusions without a hub-count
restriction. They raise the checked union from 106 to **108**, leaving **150
open types**: 102 cycle and 48 matching. The whole regular matching branch and
the unrestricted covering problem remain unresolved.

The campaign used 176.358332 solver seconds in total. The maximum per-case
total was 13.308738 seconds, below the 15-second budget. The new preflight
checked all four layouts and 100 fixed/reset transitions without solving,
rejecting 46 damaged controls. Final readback checked all 51 records and all
49 sparse primals, with six damaged controls. Exact arithmetic on the stored
binary values gave a largest numerical row residual of about `4.4982e-12`.
The primals have 392–445 fractional block values; these numerical solutions
are not exact feasible witnesses or covers.

## Evidence

- Raw run: `experiments/scratch/four-seven-template-hull-refresh-screen-20261003/`.
- Results SHA-256: `a2939db2a7011cafe50d120c7f7b0e9c04176a4ba8774b100044593bd41bc6c8`.
- Readback audit SHA-256: `edd7074664d5279df69b801226749fff0c7527d35c94ed8a8c5e05b66c16f52f`.
- Matching-095 audit SHA-256: `cd07267a8ea70efe71d62fce0dbcb75f7f46b01c1c198d8970226d1cc814ffa7`.
- Matching-113 audit SHA-256: `10729b2f70eea216507fc729f82f3ff79a5ddf38bfb2cea96357234c8e515a26`.
- Refreshed catalog/matrix audit SHA-256: `af1c3224050faa086859930489e3bbce8fa5d9acaa922c6769f1c1bce528911b`.

Independent proofs are in `../four-seven-template-hull-refresh-independent/`.
The machine-readable summary records both certificate hashes, proof audit
paths, the prior checked union, and the 48 remaining matching IDs. Original
solver records retain their pending flags; this separate report records the
later independent verification. All prior catalogs and results are preserved.
