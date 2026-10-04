```text
Document:    One More Checked First-Link Exclusion
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      7e01bc28a21da57a382781be18737617b69e5ced1f1c678f7246b7d793f61032
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Result and scope

The new immutable union contains 109 excluded first-link representatives and
149 open representatives: 102 cycle and 47 matching. It adds only matching-029.
The 108 registry and all 106/108 catalogs remain unchanged. These exclusions
apply only inside the normalized regular four-sevenfold branch; the unrestricted
covering problem remains unresolved and the best verified cover remains 65 blocks.

Matching-029 has six exhaustive hub-count cases `(m4,z) in {0,1} x {0,1,2}`.
Five were already excluded by checked exact rational certificates. The missing
case `(0,2)` is now excluded by CaDiCaL and a separately accepted DRAT proof
against the independently audited restricted CNF. This is an integer proof;
the earlier numerical LP optimum and unverified CP-SAT infeasibility were not
used as exclusions.

The aggregation checker binds the CNF/model audits, all seven fixed lexicographic
block IDs, the hub count, proof tools, binary/source archive hashes, raw logs,
proof bytes and accepted receipt. It then replays the other five rational
certificates with integer arithmetic against the saved audited rows plus the
same seven fixed-block equalities. Their exact positive gaps are 332781/500000,
5201/100000, 374723/250000, 6781/10000 and 217109/1000000. Eight damaged receipt
or case-coverage controls are rejected. The DRAT checker itself is not rerun
by the aggregation audit.

The five compact LP certificates are retained here. The 274,200,211-byte DRAT
proof and large audited CNF remain in ignored scratch and are bound by SHA256.
The new union points to `audit.json`; that audit binds the immutable receipt.
Running `uv run python experiments/2026-10-03/four-seven-template-drat-exclusions-109/check.py`
replays this aggregation without solving again.

# Timing and recovery

CaDiCaL 3.0.1 reported 192.38 seconds real time for matching-029. Its status was
written to `solution.sol`, not stdout, so the original wrapper stopped before
saving Python timing. The solver was not rerun. The recovered receipt leaves
Python elapsed/start fields null, keeps the native rounded time and explains
the recovery. DRAT-trim accepted the preserved proof with exit 0 and the exact
line `s VERIFIED`, taking 264.733337 seconds of measured wall time.

The original matching-063 ASCII run reached its 300-second limit: measured
wall time 300.078952 seconds, exit 0, saved UNKNOWN status and 343,322,046 bytes
of partial proof. It has no checker acceptance and remains open.
