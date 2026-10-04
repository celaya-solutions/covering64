```text
Document:    Fixed-Link and Hub-Case Boolean Template CP Pilots
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      287f3b38797330307216e764d1db5016c1b8ad934ee3e2701b630fe1b0ef757d
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Restricted template CP pilots

Two frozen construction models retain every field of the independently audited 106-version matching Boolean-template CP model. Each adds exactly nine linear equalities and no variables, giving 55,528 Boolean variables and 4,559 constraints.

| First-heavy link | Hub subcase (m4,z) | Seven fixed block variable IDs |
| --- | --- | --- |
| matching-029 | (0,2) | 0, 4, 26, 38, 47, 63, 77 |
| matching-063 | (0,1) | 3, 4, 18, 29, 39, 61, 67 |

The first seven equalities select the exact representative's heavy blocks in original lexicographic order. The eighth fixes the number of blocks containing all four hubs to zero. The ninth fixes the sum of C(h,3) over selected blocks, where h is a block's hub count, to six for matching-029 and five for matching-063. Equivalently these are the already audited hub-count subcases m4=0,z=2 and m4=0,z=1.

Both first links remain open in the independently checked 108-exclusion registry. Each has five prior exact hub-case exclusion proofs; the chosen subcase is the sole remaining case in that six-case partition. The manifest binds those five proof paths and hashes for each ID, the original orbit catalog, priority plan, current selection registry, exact fixed blocks and IDs, added rows and base/model hashes.

The base deliberately remains the audited 106-version complete-template model. The later 108 registry only governs pilot selection. No new catalog deletion, relabeling assumption or symmetry normalization is applied here. These are two restricted construction pilots, not a completeness claim over all first links or an unrestricted covering-number encoding.

`build.py` makes no solver calls and rejects changed input hashes or changed base fields. The independent nine-row audit passed both models and rejected 16 damaged controls. The preceding whole-branch campaign finished before the approved sequential 600-second, eight-worker pilots launched. Any candidate must pass both covering verifiers, with their exact outputs preserved. UNKNOWN or uncertified CP-SAT INFEASIBLE remains inconclusive.

## Completed bounded observations

Both pilots ended early with CP-SAT INFEASIBLE: matching-029/(0,2) after 27.930858 seconds and matching-063/(0,1) after 37.413588 seconds. Their seeds were 2026103801 and 2026103802. Both saved parameter protos specify 600 seconds and eight workers; they ran sequentially. Neither returned a witness.

These statuses have no independently checked proof certificate and do not change the exact exclusion registry, which remains at 108. `collect.py` independently parsed and bound the saved solver responses, parameters, scope fields and hashes without solving again. `pilot-audit.json` passed; `pilot-evidence.json.gz` preserves complete responses and supporting metadata in 13,356 bytes. An independently checked exact certificate would be required before either conditional case could enter the exclusion chain.
