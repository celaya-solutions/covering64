```text
Document:    Native Compact Pair-Two Hint Pilot
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      463bcd0c8255ab310fd6982109699f8fc9e6dc40482d912b97450416d9d67d30
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```
# Stronger pair-deficit hint pilot

This isolated pilot seeks a 64-block partial family satisfying all 10,920 stronger pair-two-triple rows. It stops at the first real zero-deficit hint. Positive holes remain an incomplete family; a covering claim requires zero holes and both verifiers. No second optimization phase is part of this pilot.

For each pair, the compact deficit is `max(0,12-3c(P)+top1+top2)`, using the largest two values from its 14 distinct triple positions, including equal count values at different positions. D2max sums these 120 maxima. The exact aggregate is zero if and only if all 10,920 explicit rows are satisfied; it is generally smaller than their full deficit sum. The independent proof audit is `796bf612ebe939bad5d346c3ac4348ab77b072c12c987f35b5e09647fef64e22`, bound by manifest `117a3260f137fd45cded1757b1b20cab0541b647bcb896ed55329cebb959a2c2`.

All 64 blocks are mutable, all 4,368 lexicographically ordered blocks remain eligible, and four independently audited core overlaps are capped at 55 before mutation. There is no fixed degree or hard pair floor. The original three-cap/pair helpers are copied byte-for-byte; a separate adapter adds the fourth core. A move recomputes only the union of pairs in its removed and added blocks, including shared pairs with unchanged pair counts. At most 20 pairs times 14 positions are inspected. D3, D4, minimum pair count, the full stronger-row deficit sum and global-profile status are separately recounted on saved states and audits.

Acceptance uses exact integer energy `20*D2max+H`, with the energy difference divided by 20 before applying the existing temperature schedule `0.06+(0.7+0.1*(restarts mod 4))*(1-step/1500000)^3`. Best and restart states use the lexicographic key `(D2max,H)`, with the first tie retained. Every third restart uses the assigned initial family; others use the best primary record. One uniform value is consumed per proposal. Restart spans are 1,500,000 proposals and periodic audits occur every 4,096 proposals.

Raw profile-clear hole best, lexicographic primary best, the first qualified hint and current are saved separately. Primary traversal and records may have a forbidden profile; that status is reported rather than silently filtering the primary score. An actual zero D2max state is immediately fully recounted. Positive H emits `qualified_hint_found`; zero H emits a candidate-cover status that the recorder must confirm using both verifiers. Ordinary and interrupted exits retain current, raw and primary best; a missing qualified record is null.

| Planned seed | Assigned initial H | D2max | Full row deficit sum | Four core overlaps |
| --- | ---: | ---: | ---: | --- |
| 2026104501 | 48 | 75 | 175 | 0, 1, 1, 12 |
| 2026104502 | 49 | 74 | 170 | 0, 2, 2, 4 |

The pilot permits at most two sequential calls of at most 60 seconds each. It stops the entire campaign at the first actual zero D2max, skipping later seeds. No time is reallocated. Each call has a 75-second watchdog, 5-second termination grace, and no relaunch. The recorder stores actual optimizer call count, stop reason, and skipped-run reasons.

Preparation used no optimizer calls. ASan/UBSan direct controls passed 2,505 moves, 1,670 accepts, 790 rollbacks, 40 duplicate rejects, four pre-mutation cap rejects, 12 cap boundaries, ten shared-pair cases and two exact Metropolis threshold cases. Arithmetic controls included 3,000 top-two profiles; 135,762 scalar status/stop cases test control flow only and are not candidate witnesses. No genuine zero-D2 64-family was available as a positive end-to-end control at preparation. Forged zero caches and false qualification/cover statuses are rejected by full recount. Malformed input and watchdog controls also passed. Both starting families and all saved direct-control families were recounted by both verifiers.

The frozen manifest is `fc6db0facd6e144fee319e33da869c9e9e013db2d4b92f12787700be5438b11e`, native source `3f59f8b04e2ad78a8ff37feceee0d42acd0cdd930021c44e5e0b52836c3e96e9`, binary `9503877f087fe6306744923a91bead987da4d451cc029933722ed8f98a2bcf60`, runner `7c134a474e1805d491f2bae8fd1232a1e4160ce7e4cc6ced9345a9cbbba3804f`, and controls `1bc6f734a9655d9c6a638db5b5e3728c0a76a89e0b606f300ef4ae31d5e23301`.

## Completed outcome

The independent gate passed before launch, with SHA256 `8990dff2efb2ba9ec51daa3855dc6aaaf445d0e2f38dda296f36c1c79be33301`. Its separate ASan/UBSan controls covered 1,306 direct recounts, 522 commits, 530 rollbacks, 48 duplicate cases, four cap rejections, 96 shared-pair contribution changes, 98,304 tied-position profiles, 31,521 extremal profiles and 4,488 scalar flow cases. Of the accepted states, 122 had pair count below five, directly checking that no hard pair floor had been introduced.

Both permitted optimizer calls completed because the first did not find a qualified hint. Each native process exited 1 with `finished` status. The recorder exited 0 and recorded two actual calls, no skipped seed, stop reason `budget_exhausted`, and no budget reallocation. Neither watchdog fired, both validation-error fields are null, and neither run rejected a proposal at a core cap. All 128 saved records were checked; 115 distinct families are represented.

| Seed | Wall seconds | Proposals | Restarts | Best primary D2max | Primary holes | Full row deficit sum | Raw best holes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026104501 | 60.004893791 | 126,405,504 | 85 | 46 | 33 | 267 | 33 |
| 2026104502 | 60.005936291 | 128,184,032 | 86 | 56 | 59 | 510 | 47 |

The first primary winner is [the 33-hole partial family](seed-2026104501/search-final-primary.txt), SHA256 `9ad3b39d11872c61f6a7bc3f3e85c70c630be6ea7455f339a2b0ca865f83b4b1`. It has D3=28, D4=24, minimum pair count 4, and four core overlaps [0,3,2,0]. Its raw and primary records coincide.

The second primary winner is [the 59-hole partial family](seed-2026104502/search-final-primary.txt), SHA256 `54e46f450492a28c06c57cca5d6a9fd811b19dbbb4c00f987ce9b8bbde6b4687`. It has D3=52, D4=48, minimum pair count 4, and core overlaps [1,1,2,0]. The separately retained [raw 47-hole family](seed-2026104502/search-final-raw.txt), SHA256 `9b594470adf306fc9b54ea52242091a0ea1ff7e0f207e1c0c23a3fc9605189ee`, has D2max=75 and full row deficit sum 165, but D3=D4=0, minimum pair count 5 and core overlaps [0,2,2,4]. Its old-cut zero status does not qualify it for this stronger target.

The final current states are also retained. Seed 2026104501 ended with H=102, D2max=80, full row deficit sum 635, D3=26 and D4=37. Seed 2026104502 ended with H=80, D2max=73, full row deficit sum 642, D3=52 and D4=52. Both final current states have minimum pair count 4. Every final current, raw and primary family has a clear global profile. Qualified records are absent in both runs.

The compact scores improved from 75 to 46 and from 74 to 56, while the primary winners' full row deficit sums increased from 175 to 267 and from 170 to 510. This matters for interpreting the objective: compact and full scores have equivalent zero sets, but positive compact-score improvement need not improve the total row deficit. The primary winners also lost the starts' D3/D4-zero property, which was intentionally not a hard search restriction.

The independent postcheck passed all 115 distinct families with 230 fresh verifier calls, plus direct metric recounts, raw-log/final-role checks, frozen source/archive validation and campaign-budget checks. Its receipt SHA256 is `a14a9b02fcd6915e82ece0a16941a21f9f8b71e6af5383765c2cb6fd6d1d3486`. The completed result SHA256 is `e433f4264066158a228ff5ec3f4b158e3114e689f0c6a78125ea3f72ab668b07`.

No zero-D2 qualified hint or cover was found. No second optimization phase, extension or extra call occurred. The bounded failure is inconclusive and gives no lower-bound or nonexistence result.
