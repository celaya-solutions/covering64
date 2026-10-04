```text
Document:    Independent Native Fixed-Link Search Gate
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      af3487c33f504ffd8cca84d67e9ebe03fe733c658d190a1a0bb3261d3978fceb
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Native search gate

The frozen C++ source `e3c13c3d7bac16cc9318663539f0d5c3cdcfb7c5a64740e898c17bd529f0722c` passed static review and independent dynamic checks.

`check.py` independently recounted 157 archived states: 153 smoke snapshots and four seed states. It checked 64 distinct blocks, all point degrees, the exact fixed anchor link, uncovered triples, filenames and final hole claims. It replayed 18 saved operations and all forced rollbacks. The sibling auditor also ran both covering verifiers for every saved smoke state.

The checker rebuilt the exact frozen source using warnings as errors, AddressSanitizer and UndefinedBehaviorSanitizer. Four fresh bounded runs exercised all three move modes and exact rollback. Five additional malformed seeds were rejected. No compiler or sanitizer diagnostics appeared.

This clears only the planned four 300-second, single-thread heuristic pilots, with at most two native processes at once. Seed cyclic structure is not imposed on subsequent states. Reachability is not proved; exhaustion cannot exclude any case. Any actual cover must pass both package and standalone verifiers.

The raw fresh sanitizer binary, logs and states are in the ignored `experiments/scratch/fixed-link-profile-independent` directory. `audit.json` preserves commands, input hashes, counters and state hashes. Parent owns integration and commits.

## Completed bounded pilots

`check_pilots.py` independently recounted all 264 saved pilot states and replayed all 60 saved operations, including every forced rollback. The four 300-second runs ended with 17, 17, 20 and 18 uncovered triples. No cover was found. The separate sibling audit preserves complete outputs from both covering verifiers for all 264 states. `pilot-audit.json` records this independent readback.
