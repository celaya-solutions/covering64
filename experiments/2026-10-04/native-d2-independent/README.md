```
Document:    Native Compact Pair-Two Pilot Independent Gate
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      117a8bf9e0312677156237bc65c37334707360b8ed65fbdb4a15d300bd887d90
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Native compact pair-two pilot: independent gate

The frozen source and runner pass this gate for the exact bounded pilot authorized by root: seed 2026104501 starts from H48; if it does not find a zero-D2max hint, seed 2026104502 starts from H49. Each receives a nominal native budget of 60 seconds. The runner records actual elapsed time separately, has a 75-second watchdog and 5-second termination grace, and does not reallocate unused time. The whole pilot ends at the first actual zero score. A positive-hole result is a qualified hint; a cover still requires both verifiers. No optimizer was called by this audit.

## Checked implementation

The top two triple counts use distinct positions and retain equal values. The union of pairs in the old and new blocks includes shared pairs whose pair counts remain unchanged while triple counts change. All commits and rollbacks agree with an independent direct recount of every one of the 10,920 rows. The objective is 20*D2max+H, with acceptance changes divided by 20. Best states and restarts use lexicographic (D2max,H), with the original start every third restart. Raw profile-clear records remain separate. There is no hard pair floor, fixed degree condition, or soft profile penalty.

All 4,368 lexicographic blocks, 560 triples, 120 pairs, and four 60-block core membership tables are checked. The fourth core was independently reconstructed from the original core and the audited point permutation; the first three tables inherit their prior checked receipts. All four hard caps are 55.

## Controls and saved-state paths

The independent C++ controls are rebuilt with address and undefined-behavior sanitizers against the exact frozen source. They pass 1,306 complete state recounts, 522 accepted moves, 530 rollbacks, 48 duplicate rejections, four cap-56 rejections, and 96 shared-pair contribution changes. There are 40 proposals at each old/new block intersection size from zero through four. In 122 accepted states, the minimum pair count is below five, directly checking that no hard pair floor was introduced.

Metric controls check 98,304 tied-position profiles and 31,521 compatible extremal profiles. Another 4,488 scalar cases check stopping and status selection. The controls reject forged zero metrics, damaged counts/contributions, damaged fourth-core counts, duplicate state data, false cover/hint statuses, and forged qualified records. They check raw versus primary recording, tie retention, restart selection, and normal/interrupted final saves. Every saved control file is independently recounted. These saved controls reuse the two previously double-verified input families.

No actual zero-D2max 64-block family was available as a positive end-to-end stop control. The successful-zero branch has exhaustive scalar controls and source review, not an invented candidate witness. Production preparation separately passed malformed-input, watchdog, direct-move and recorder controls; their frozen receipt and all inputs are hash-bound by the gate.

The runner checks every saved state with the package verifier and standalone checker, asserts the complete metric vector, saves actual call counts, and writes skip reasons. The independent gate does not establish that the pilot will succeed or prove infeasibility if it does not.

| Start | Holes | D2max | D2sum | Four core overlaps |
| --- | ---: | ---: | ---: | --- |
| H48 | 48 | 75 | 175 | 0, 1, 1, 12 |
| H49 | 49 | 74 | 170 | 0, 2, 2, 4 |

`gate.json` binds the producer manifest, source, runner, binary, independent source, controls and raw files. `check.py` reproduces the independent pre-run gate and never launches the optimizer. Frozen inputs must not change after GO.
