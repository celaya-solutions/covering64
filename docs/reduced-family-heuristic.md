```
Document:    Joint Reduced Multiplicity-Seven Family Search
Version:     v1.3.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      afe000ed72cb2a13f81e6d6724ebd11ce461fbd00466aa3b5dfa4a1f03fb3ad2
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Result

The completed v1.1 900-second trade campaign reduced the 14-hole starter to five holes. It did not find a cover. Its best witness is `experiments/2026-10-03/reduced-family-heuristic/trades-2026100362/search-improvement-24-h5.txt`, with SHA256 `187d3a77caf046d31483ef5b06ed0571d3fa0e367c7726b054d1db774d342903`. Both cover verifiers agree that it is incomplete.

The five-hole state fails necessary full-cover conditions: its fixed local families have hub pair-row lower bound 25 against budget 24, and its four sevenfold plus one sixfold triples have weighted count `4*4 + 3*1 = 19 > 16`. Three saved six-hole alternatives pass the heavy-count and scoped five-heavy filters, but they retain the same family-row overflow. Passing any listed subset of necessary checks does not prove that a state can be completed.

Both v1.2.1 soft-penalty campaigns completed without a cover. The 900-second run with weights four/four retained six raw holes and reached thirteen holes passing its scored filters. The 600-second continuation with weights eight/twelve reached five raw holes, six heavy-qualified holes, and thirteen holes passing its scored filters. All 24 and 15 saved states, respectively, passed the independent metric audit and both cover-check consistency checks. The thirteen-hole states still fail broader hub necessities: a repeated hub belongs to a different heavy triple. The v1.3 score below includes those rules.

The completed v1.3 campaign found five raw holes and twenty holes passing every expanded scored necessity. It did not find a cover. All 29 saved snapshots passed both cover-check consistency checks and the independent metric audit. This is a bounded search outcome in the normalized regular branch, not an impossibility result.

A second 600-second v1.3 run started from that fully scored-qualified twenty-hole state, using the same frozen binary with weights six/four and a new random seed. It made no improvement. All ten saved snapshots passed the same dual-verifier and metric checks. Neither run establishes a minimum hole count, a lower bound for the covering number, or an unrestricted impossibility claim.

# Frozen first pilot

The frozen v1.0 300-second joint native pilot reduced its normalized 27-hole starter to 14 missing triples. It did not find a cover. The best local families have four holes, zero holes, and four holes, respectively. All 64 blocks are distinct, every point has degree 20, and the seven blocks through triple `{1,2,3}` have the normalized `P3 + 5K2` outside edges.

The best snapshot is `experiments/2026-10-03/reduced-family-heuristic/pilot-2026100361/search-improvement-17-h14.txt`. Its canonical SHA256 is `1e26105bfcee33ac6885eba503c3a673b5dd095c06851ff7508af2637b4f5da4`. Seven pairs still have multiplicity four; its pair histogram is `{4:7, 5:75, 6:29, 7:9}`. Both cover verifiers agree on the 14 missing triples and reject it as incomplete. This is progress within the reduced family, not a new global best near-cover claim.

# Search

The state consists of three 13-quadruple local families and 18 outside five-blocks. Each local family comes from the verified plane, four-hole, or six-hole template, relabeled so its missing matching is contained in the seven allowed edges. The fixed seven blocks and these families cover every triple touching points 1, 2, or 3. Therefore the objective is exactly the number of missing triples among the 286 outside triples.

Every family remains degree four. The outside blocks keep degree six at point 4 and seven at every other outside point. In v1.0, seventy-five percent of outer proposals exchanged exclusive points between two outside blocks, usually targeting a missing triple. Twenty percent applied compatible label transpositions or matching-edge exchanges to a whole family. Five percent resampled a plane, four-hole, or six-hole family and made 64 greedy targeted outside-swap repair proposals before accepting or rejecting the combined state. No private-triple or point-essential restriction is imposed.

The annealing temperature cycles from 3.65 to 0.15 over 200,000 outer proposals. Every million proposals restarts from the best state in v1.0. Both accepted and proposed states preserve distinct blocks and the degree conditions. Full recounts audit saved states, the first rejected move of each kind, and periodic intermediate states. Missing-triple indexes and full coverage counts are rebuilt independently inside the native audit.

# Small trades and diverse states in v1.1

The new move exchanges four or six local blocks between an r4/r6 family and a nearby projective plane. The saved maps are nearest only among the 72 planes sharing the normalized point-13 star; no global nearest-plane claim is made. If the current family is `e(R)` and the saved plane is `f(P)`, the forward move is `e(f(P))`. The reverse move uses `e(h(f^-1(R)))`, where `h` is one of all 5,616 point automorphisms of the canonical plane. Enumerating these maps uses exact pair counts and partial-block containment, and every full map is checked against the entire target block set.

The state records each family's template and full point permutation. Compatible permutations compose with that embedding, and a full recount checks that its image equals the actual family. Reverse trades are indexed by their missing matching, so the search can select those whose holes lie inside the allowed seven-edge graph. Startup checks require overlap of exactly nine blocks for r4 and seven for r6. The regression test separately reads before/after witnesses and requires an actual four- or six-block local exchange.

The v1.1 proposal mixture is 65% outside swaps, 20% compatible family permutations, 5% fresh families, and 10% small trades. Both fresh families and small trades receive 64 greedy outside repair proposals. The annealing objective remains the exact number of uncovered outside triples. Half of the periodic restarts use the best state and half use a bounded reservoir. At most eight additional states per hole count are saved, within one hole of the best at the time of saving, and at block-set distance at least four from every live reservoir entry. These are distinct block sets; they are not claimed nonisomorphic.

Every saved state and each 45-second progress event also reports an independently tested necessary condition for the fixed local families. For each outside pair `xy`, let `m_xy` be the number of triples `xyz` not covered by the local families. Each outside block containing `xy` covers at most three of them, so an outside completion needs pair multiplicity at least `ceil(m_xy/3)`. The sum of these lower bounds at a point cannot exceed 24 at the hub or 28 elsewhere. An overflow rules out completing those fixed families; the search still permits the state as an intermediate and can change its families.

# Optional penalties in v1.2.1

Let `n6` and `n7` count triples of exact multiplicity six and seven, including the fixed sevenfold triple `{1,2,3}`. Define the heavy penalty as

`max(0, 4*n7 + 3*n6 - 16) + 5*sum(max(0, multiplicity-7)) + forbidden_five`.

Here `forbidden_five` is one only when five pairwise disjoint triples have multiplicity at least six and at least two of those five have multiplicity at least seven. A profile with just one sevenfold and four sixfold triples does not trigger this term. The coefficient five on multiplicity above seven is a search weight, not a theorem coefficient. The separate family penalty is the sum of positive pair-row overflows. The score is exact holes plus the two weighted penalties; neither penalty rejects a state or removes a move.

The new campaign uses weights four and four, RNG seed 2026100363, one native process, and a 900-second budget. It starts from the independently checked six-hole `search-diverse-30-h6.txt`, copied as `inputs/seed6-heavy-qualified.txt`. This seed passes the heavy filters but has family penalty one, giving initial score ten. The blocked five-hole witness would score 25 under the same weights.

Records are saved separately for the fewest raw holes, the fewest holes passing the heavy filters, and the fewest holes passing both scored filter sets. Records include rejected annealing proposals, so a newly observed candidate is preserved even when its score is worse. Restarts use the best score and a bounded reservoir within one score unit of it. Sevenfold link degree shapes and repeated hubs are logged as separate diagnostics. They are explicitly excluded from the score and from `passes_scored_filters`; that label does not mean all known full-cover necessities pass.

An independent mathematical source review caught an overbroad five-heavy predicate in the initial v1.2.0 draft. It was corrected before any long run of that version. A real degree-20 control with one sevenfold and four disjoint sixfold triples now checks this boundary, and another real partial control with multiplicity eight checks the separate high-multiplicity penalty. The review also checked forward/reverse trade maps, embedding updates, score caching, pre-acceptance record capture, rollback, restarts, and hub diagnostics.

# Expanded necessities in v1.3

All the following conditions are necessary only for a full regular degree-20 cover. They are soft preferences in this constructive search, and zero penalty does not establish completion or completability. The v1.2.1 archives remain unchanged. Its older qualification labels keep their original, narrower meaning.

The v1.3 heavy penalty retains every old term and adds these nonnegative integers, with coefficient one each:

| Field | Exact graded term |
| --- | --- |
| `heavy_overlap` | Sum of intersection sizes over unordered pairs of triples of multiplicity at least six. |
| `repeated_point_excess` | For each heavy triple, the positive part of its number of repeated outside points minus one. |
| `repeated_incidence_excess` | Sum of positive endpoint-incidence excess above three for every repeated point of every heavy triple. |
| `endpoint_shape_distance` | Minimum L1 distance from the sorted 13 endpoint incidences to the allowed shape below, for each exact-six or exact-seven triple. Above-seven triples contribute zero here because the separate multiplicity penalty handles them. |
| `hub_inside_heavy` | Number of incidences where a repeated hub belongs to a heavy triple, counted for each hub-bearing triple and containing heavy triple. |
| `hub_collision` | For each point, the positive part of the number of heavy triples using it as a repeated hub minus one. |
| `internal_pair_deficit` | Sum of positive deficits below seven over each heavy triple's three internal pairs. |
| `hub_internal_pair_excess` | Sum of positive excesses above seven over those internal pairs, but only for triples having at least one repeated hub. |
| `hub_cross_pair_deviation` | Sum of absolute deviations from six over the three anchor/hub pairs, for every repeated hub of every heavy triple. |
| `refined_count_overflow` | Positive part of `3*n6 + 4*n7 + h6 - 16`, where `h6` counts exact-six triples having at least one repeated hub. |
| `generic_pair_deficit` | Sum of positive deficits below five over every full-label pair. |

For exact six, the endpoint shapes are twelve singletons; one double plus ten singletons; or one triple plus nine singletons. Zeros pad each list to thirteen entries. Exact seven requires one double plus twelve singletons. Endpoint incidences count all points outside the heavy triple, including points 1, 2, and 3 when those are endpoints. In a full cover a heavy triple without a repeated hub may have an internal pair above seven; v1.3 deliberately does not penalize that through `hub_internal_pair_excess`. A repeated hub forces its three heavy internal pairs to seven and its three anchor/hub pairs to six, by the audited regular pair-excess argument.

The score remains `holes + heavy_weight*heavy_penalty + family_weight*family_pair_row_overflow`. Both old and refined count overflows contribute; this is an explicit heuristic weighting choice. `passes_heavy_filters` now requires every v1.3 heavy/hub and generic pair term to vanish. `passes_scored_filters` additionally requires zero fixed-family row overflow. The older sevenfold diagnostics remain for comparison but no longer describe the full scored hub checks.

Outside pair multiplicities are updated alongside triples and independently rebuilt during native state audits. Pairs through the fixed anchors have constant multiplicities seven, six, or five. Endpoint degrees are reconstructed from the current blocks. The independent Python auditor recounts full 16-point blocks, without using the native incremental state. It branches on metadata `score_version`, so historical v1.2.1 campaigns retain their original score definitions.

The completed run used seed 2026100366, weights one/two, and 600 seconds, starting from the prior thirteen-hole scored-qualified witness. It made 230,489,810 outer proposals and 1,395,317,376 repair proposals, with 230 restarts and one saved diverse state. All 29 snapshots were dual-verified and independently metric-audited. The four-block and six-block trades were applied 8,386,882 and 1,890,612 times. No cover was found.

The raw five-hole witness is `full-penalty-2026100366/search-improvement-24-h5.txt`, SHA256 `922c9a5424bff5c990dc482a1470acf120bc846c84297f9b1508658d4af1347f`. It has heavy penalty eighteen and family-row overflow one. The best score is eleven at the six-hole `search-score_improvement-25-h6.txt`: the remaining score penalties are one shared hub, one hub-cross pair deviation, one generic pair deficit, and one family-row overflow weighted two. Its six uncovered triples all contain point 12 and are exactly `{4,7} x {5,6,15}` joined to point 12. Both heavy triples `{5,8,11}` and `{9,13,16}` use hub 12; pair `{12,15}` has multiplicity four and hub-cross pair `{5,12}` has multiplicity five.

The best state passing all scored necessities is `full-penalty-2026100366/search-qualifying_improvement-27-h20.txt`, SHA256 `3057f9f3e72e787d58bd585a0e3fe091af84f2bc2982088fc0a785012d0ffbb7`. The separate full screen also confirms every heavy/hub condition, zero generic/internal/hub-cross pair deficits, and zero family-row overflow. It has only the fixed sevenfold heavy triple and remains incomplete with twenty holes. A different twenty-hole witness, `search-heavy_qualifying_improvement-26-h20.txt`, passes the expanded heavy/pair filters but has family-row overflow one; it must not be described as passing all scored necessities. Full manifests, screen reports, and final metric audit are in `full-penalty-2026100366/`.

The second run used seed 2026100367 and weights six/four, starting from that fully scored-qualified twenty-hole state. The same six-hole state that scored eleven under weights one/two would score twenty-eight under these weights, above the clean starter's score twenty. This changes the preferred restart state without rejecting imperfect intermediate proposals. The second 600-second run made 242,009,085 outer proposals, 1,369,268,928 repairs, and 242 restarts. It found no strict improvement or additional diverse near-best state. All ten snapshots were dual-verified and independently metric-audited. Four-block and six-block trades were applied 7,895,908 and 1,394,364 times. Its best raw, heavy-qualified, and fully scored-qualified counts all remain twenty, at the initial witness. Evidence is in `clean-penalty-2026100367/`. The starting state and random seed also differ between runs, so this is not a controlled measurement of the effect of weights alone.

The preflight full suite passed 257 tests and ten subtests, with three existing dependency deprecation warnings; frozen dependency sync and Ruff also passed. The final ASan/UBSan binary, compiled from the exact frozen v1.3 source, made 95,968 proposals in one second, exercised all four move and rollback modes, and saved fourteen dual-verified and metric-audited snapshots without diagnostics. The independent auditor matched all 31 draft snapshots and 70 historical snapshot recounts, and a synthetic noncandidate overlap fixture verified that hub containment counts each containing heavy triple. Real partial controls exercise shared hubs, hubs inside heavy triples, exact-six repeated hubs, refined-count overflow, and pair deficits. The frozen native source SHA256 is `75dde29a73b6c5e2780d972425c69c817a59df1bfed317e3b3cef9e6a10887bd`.

# Budget and evidence

The pilot used RNG seed 2026100361, one search process, and a 300-second search budget. It made 245,852,169 outer proposals and 786,462,848 repair proposals. Eleven strict improvements reached hole counts `26,25,24,22,20,19,18,17,16,15,14`. Whole-family replacement and repair was accepted 3,987,757 times out of 12,288,482 valid attempts; it was not a rare move. The run made 245 restarts and ended inconclusively.

The independent runner checks every saved snapshot immediately with a separate set-based recount, the package verifier, and `scripts/check_cover.py`. It compares every missing triple and canonical hash, checks the exact seven-block normalization, checks all local and outside degrees, and logs the high-triple multiplicity profile. All 19 pilot snapshots passed these consistency checks. The one-second sanitizer run saved another eight checked snapshots, with no sanitizer diagnostics. Four malformed native seed controls were rejected. Six focused tests and the full 228-test suite passed; the full suite reported three existing dependency deprecation warnings. Ruff passed for the new sources.

The immutable input copies, original input provenance, seeds, compiler version, source revision, source and binary hashes, event logs, and compressed candidate checks are under `experiments/2026-10-03/reduced-family-heuristic/`. The search source is `scripts/reduced_family_heuristic.cpp`; the separate recount is `scripts/verify_reduced_family_heuristic.py`. Source archives and native binaries remain outside Git under `experiments/scratch/reduced-family-heuristic-20261003/`.

The completed v1.1 trade campaign made 281,893,082 outer proposals and 1,853,728,576 repair proposals. Its five strict improvements reached `13,12,9,7,5`; it made 281 restarts and saved 22 diverse states. Four-block trades were applied 11,310,305 times and six-block trades 3,559,924 times. All 37 snapshots were independently recounted and checked by both cover verifiers. The standalone `audit_campaign_metrics.py` additionally reconstructed every saved pair-row metric and every diversity-distance claim.

Final v1.2.1 validation passed 242 tests, with three existing dependency warnings, and Ruff. The one-second ASan/UBSan control made 114,934 outer proposals, exercised all four move and rollback modes, and produced no sanitizer diagnostics. All 11 snapshots were dual-verified; the separate metric auditor also checked their heavy counts, correctly scoped five-heavy flags, scores, qualifications, pair-row bounds, hub diagnostics, and recorded minima. The frozen native source SHA256 is `4f9df6eae2cff4545cc3c9738332705918fb7b0a252b2203f217d35334a531f8`.
