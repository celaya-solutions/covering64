```
Document:    Joint Reduced Multiplicity-Seven Family Search
Version:     v1.2.1
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      d599bd715cf4ad5f00e2904813f3115f8c24ae1df4353a66ddf932357cdfb75b
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Result

The completed v1.1 900-second trade campaign reduced the 14-hole starter to five holes. It did not find a cover. Its best witness is `experiments/2026-10-03/reduced-family-heuristic/trades-2026100362/search-improvement-24-h5.txt`, with SHA256 `187d3a77caf046d31483ef5b06ed0571d3fa0e367c7726b054d1db774d342903`. Both cover verifiers agree that it is incomplete.

The five-hole state fails necessary full-cover conditions: its fixed local families have hub pair-row lower bound 25 against budget 24, and its four sevenfold plus one sixfold triples have weighted count `4*4 + 3*1 = 19 > 16`. Three saved six-hole alternatives pass the heavy-count and scoped five-heavy filters, but they retain the same family-row overflow. Passing any listed subset of necessary checks does not prove that a state can be completed.

The v1.2.1 soft-penalty campaign is in progress at this checkpoint. Its final status and all witnesses belong in `penalty-2026100363/metadata.json` and the independently checked event log; no outcome is claimed here before completion.

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

# Budget and evidence

The pilot used RNG seed 2026100361, one search process, and a 300-second search budget. It made 245,852,169 outer proposals and 786,462,848 repair proposals. Eleven strict improvements reached hole counts `26,25,24,22,20,19,18,17,16,15,14`. Whole-family replacement and repair was accepted 3,987,757 times out of 12,288,482 valid attempts; it was not a rare move. The run made 245 restarts and ended inconclusively.

The independent runner checks every saved snapshot immediately with a separate set-based recount, the package verifier, and `scripts/check_cover.py`. It compares every missing triple and canonical hash, checks the exact seven-block normalization, checks all local and outside degrees, and logs the high-triple multiplicity profile. All 19 pilot snapshots passed these consistency checks. The one-second sanitizer run saved another eight checked snapshots, with no sanitizer diagnostics. Four malformed native seed controls were rejected. Six focused tests and the full 228-test suite passed; the full suite reported three existing dependency deprecation warnings. Ruff passed for the new sources.

The immutable input copies, original input provenance, seeds, compiler version, source revision, source and binary hashes, event logs, and compressed candidate checks are under `experiments/2026-10-03/reduced-family-heuristic/`. The search source is `scripts/reduced_family_heuristic.cpp`; the separate recount is `scripts/verify_reduced_family_heuristic.py`. Source archives and native binaries remain outside Git under `experiments/scratch/reduced-family-heuristic-20261003/`.

The completed v1.1 trade campaign made 281,893,082 outer proposals and 1,853,728,576 repair proposals. Its five strict improvements reached `13,12,9,7,5`; it made 281 restarts and saved 22 diverse states. Four-block trades were applied 11,310,305 times and six-block trades 3,559,924 times. All 37 snapshots were independently recounted and checked by both cover verifiers. The standalone `audit_campaign_metrics.py` additionally reconstructed every saved pair-row metric and every diversity-distance claim.

Final v1.2.1 validation passed 242 tests, with three existing dependency warnings, and Ruff. The one-second ASan/UBSan control made 114,934 outer proposals, exercised all four move and rollback modes, and produced no sanitizer diagnostics. All 11 snapshots were dual-verified; the separate metric auditor also checked their heavy counts, correctly scoped five-heavy flags, scores, qualifications, pair-row bounds, hub diagnostics, and recorded minima. The frozen native source SHA256 is `4f9df6eae2cff4545cc3c9738332705918fb7b0a252b2203f217d35334a531f8`.
