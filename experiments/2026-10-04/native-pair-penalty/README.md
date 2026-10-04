```text
Document:    Native Pair Penalty Pilot
Version:     v1.2.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      f0b3476f1cb531e24ac41e6a51ac9e6c325ff979e1012aee53b25e26a3823396
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```
# Native pair penalty pilot

This construction experiment starts from the checked six-hole family with 64 distinct blocks. Every slot is mutable and all 4,368 lexicographically ordered blocks remain eligible. The three previously audited core overlaps are capped at 55 before a move mutates any state. No point degrees or minimum pair count are fixed.

The exact integer energy is `20H + 5D3 + D4 + 160F`, where H counts uncovered triples, D3 sums all 1,680 pair/triple deficits `max(0,13-3c(P)+c(T))`, D4 sums all 10,920 pair/quad deficits `max(0,12-3c(P)+2c(Q))`, and F is the existing global five-heavy profile indicator. These penalties are soft. A zero-D3/D4 record can still have uncovered triples; only a zero-hole family checked by both verifiers is a cover.

A replacement recounts rows only for pairs contained in the removed or added block, including shared pairs whose net pair count is unchanged. Any changed triple or quad lies in one of those two blocks, so every row that can change has its pair in this union. At most 20 pairs and 2,100 rows are revisited per move. Rejected moves reverse all affected counts; hard-cap and duplicate rejection happen before mutation.

Profile-clear records are kept separately for lowest hole count, best soft-score tuple `(energy,D3+D4,holes)`, and lowest hole count among zero-D3/D4 states. Equal keys keep the first state. Every third restart uses the original hint; other restarts use the best soft-score record. The current state is saved on normal, interrupted and cover-found exits, even when its profile is forbidden. The common finish event retains counters and distinguishes an absent zero-deficit record with null.

The hint has six holes, D3=4, D4=0, energy 140, minimum pair count 5, and named core overlaps [2,2,0]. At preparation, screening all relabelings of the original core was inconclusive for this hint. A later independent replay proves its maximum overlap with a relabeled original core is 59; the exact hard restrictions in the frozen pilot remain only the three named core caps. D3=0 would imply pair minimum at least 5, but no extra hard pair floor is imposed.

Preparation completed without optimizer calls before the independent gate. The sanitizer controls passed 2,505 independently recounted transitions, including all replacement intersection sizes 0 through 4, ten shared-pair controls, 1,639 accepts, 817 energy rollbacks, 44 duplicate proposals, three hard-cap boundary rejections and ten reset controls. The full block subset tables, all 12,600 deficit rows, slack boundaries, damaged caches, malformed families, record eligibility, restart policy and final status paths were checked. ASan and UBSan reported no diagnostics. A real qualified 64-block control is not known, so the absence path and rejection of forged totals are tested explicitly.

The authorized optimization budget was two sequential 60-second calls with seeds 2026104401 and 2026104402. Each process has a 75-second watchdog and 5-second termination grace, with no relaunch. The recorder requires an independent gate bound to the frozen manifest, verifies every frozen input, archives sources and gate, and uses both the package verifier and standalone checker for saved candidates. Source, executable, compiler, controls and parameters are bound by the manifest. Both optimizer calls started only after independent GO. The independent review added 901 direct recounts, 360 accepted commits, 337 rollbacks, three duplicate cases and 40 replacements of each intersection size 0 through 4, with clean ASan/UBSan results.

## Completed outcome

Exactly two authorized optimizer calls completed. The recorder exited 0; both native searches exited 1 with `finished` status, no watchdog action, and no validation error. There were no retries or extensions. All 21 saved snapshot records were checked by the package verifier and standalone checker; 12 distinct families are represented.

| Seed | Native wall seconds | Proposals | Restarts | Raw best holes | Best zero-D3/D4 holes | Final current H/D3/D4 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 2026104401 | 60.012017292 | 37,532,768 | 26 | 6 | 48 | 7 / 3 / 0 |
| 2026104402 | 60.005362500 | 38,683,744 | 26 | 6 | 49 | 6 / 4 / 0 |

Neither run rejected a proposal for exceeding a named core cap. The best raw and soft-score records both remain the original six-hole hint with D3=4, D4=0 and energy 140. The final current states were retained separately, including a distinct six-hole family in the second run that tied the old score.

The first run's best zero-deficit partial family has 48 holes, D3=D4=0, minimum pair count 5, named core overlaps [0,1,1], and no forbidden global profile. Its SHA256 is `630461e4c8805916ac515114b308d6ed05b2a43da16605ea452150d7e3a784d3`; see [the checked family](seed-2026104401/search-final-qualified.txt). The second run's corresponding family has 49 holes, named core overlaps [0,2,2], and SHA256 `a7feb783eb9f36e710feba5356857514cde146104b95de03fa47716126afd9c4`; see [the checked family](seed-2026104402/search-final-qualified.txt). Both satisfy the two single-pair deficit families used in this experiment. They remain incomplete, and this does not imply they satisfy stronger pair-two-triple rules.

A zero-deficit family first appeared in the first run at native time 8.63203 seconds and proposal 4,921,893, then improved from 64 to 48 holes. The second run first recorded one at 7.39704 seconds and proposal 4,874,829, then improved from 51 to 49 holes. The new record path is now exercised by real families, although no such family was available for the pre-run positive control.

The completed result SHA256 is `7de037bb21bfc9545c9c72159a77e1df50b2f44b2c8ed555e81270853e3be785`. The frozen manifest remains `5589079bf03991d4eca468d5f45444f11427e9ce12e53946bdbd55a6d7745fe2`, bound by gate SHA256 `347af6676a0afc6aaa68d3a39b4f46fad8e0f29e46374b3c8ec60900e7e4237b`. The independent postcheck passed all 21 records across 12 distinct families with 24 fresh verifier calls, source and archive checks, and full metric/record-role agreement. Its SHA256 is `7c58bbd14d7a07dafd92fa776e23adcc7d24cd1d2c622755da8c6b7454c8ca32`.

A separate independent replay now proves that the six-hole hint has global maximum overlap 59 with point relabelings of the original 60-block core. Its audit SHA256 is `d57afcefda39021a131529bafda5a9ba8e22188ab671ee610bae058dbe5ffefb`, and its manifest SHA256 is `9c09360c28c5b2de82565e6020ac6a4ef1338a8a3a06c90072322ddd4976b042`. The transported fourth cap was not added to this frozen pilot.

## Qualified-family relabeling check

Both final zero-deficit families pass the existing audited complete necessary-partition filter: neither has five disjoint triples whose total `max(0,6-count)` is at most 4. This certifies overlap at most 55 with every point relabeling of the particular original 60-block core. The 48-hole family required two enumeration nodes; the 49-hole family required one. For the latter, every triple has multiplicity at most 5, so every five-triple deficit sum is at least 5, giving an additional elementary certificate. The separate 242-image checks each have maximum observed overlap 5; that limited check is not the basis for the all-relabel conclusion.

The read-only receipt is [post-relabel-screen.json](post-relabel-screen.json), SHA256 `b8df3a3816e9c95edc82229e6bb9348bc2e7f50b555be0b338dae5673f164d8b`. It binds the two witness hashes, their independent covering-verifier receipts, scanner SHA256 `9cdcd511eb94954bb45c1cf209c5d51517b46c11e46b44a22ce7221d9309f74a`, and filter-proof SHA256 `dff87420f7dace9498134726725ce6589c306dc01130335a1c868581545872a4`. No optimizer was called for this screen. Both families have pair-count histogram {5:85, 6:30, 7:5} and point degrees from 19 to 21, as observed rather than fixed.

No cover was found. These bounded runs are inconclusive and give no lower-bound or nonexistence result. The frozen native core-cap v2 sources are copied byte-for-byte under separate names and remain unchanged.
