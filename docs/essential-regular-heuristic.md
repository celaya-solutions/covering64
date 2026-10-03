```
Document:    Point-Essential Regular Near-Cover Search
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      e834960637e2ed3f7dd314f6652bcfb40b107b42edc662f6567e5b413e18a487
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Point-essential regular near-cover search

The search found seven pairwise nonisomorphic eight-hole near-covers with 64 distinct blocks. Every point occurs exactly 20 times, every pair occurs at least five times, and every block-point incidence belongs to a private triple. A private triple occurs in exactly one selected block. These are incomplete covers, saved as hints for exact search.

The first seed differs from the earlier pair-feasible five-hole seed in eleven blocks. Its pair histogram is 92 pairs of multiplicity five, 16 of multiplicity six, and 12 of multiplicity seven. Both cover verifiers report 552 of 560 triples covered. The independent private-triple check reports zero unsupported incidences.

## Bounded campaigns

The initial pilot used seed 2026100317 for 300 seconds. A 60-second diversity pilot used seed 2026100318. Six additional 60-second runs started from distinct saved variants, with seeds 2026100321 through 2026100326. All ran sequentially on one search process. The eight campaigns totaled 720 seconds and 1,213,846,989 proposals. None produced a seven-hole point-essential pair-feasible state or a complete cover.

Moves preserve point degree twenty by exchanging one or two exclusive points between blocks, or cycling points among three blocks. Some proposals target missing triples; others target unsupported block-point incidences. Cyclic objective weights trade off holes, unsupported incidences, and pair deficits. Ten holes is a campaign ceiling, not a mathematical restriction on unrestricted search.

Version 1.1 retains equal-score point-essential pair-feasible candidates when they have distinct label-invariant fingerprints. A fingerprint combines triple and pair multiplicity histograms, the histogram of private triples per block, and sorted missing-triple degrees. Different fingerprints prove nonisomorphism. Equal fingerprints do not prove isomorphism, and the seven saved classes are not claimed to exhaust eight-hole states.

## Plateau diversification

Version 1.2 adds atomic point cycles across four to eight distinct blocks, using five percent of proposals in total. The existing three-block cycles and two-point exchanges each retain five percent. All cycle outputs remain distinct five-element blocks and preserve every point degree. Before/after snapshots independently check one proposed cycle of each length, and rollback audits check rejected cycles. Control snapshots may exceed the ten-hole ceiling; they are proposed states, not accepted search states.

The restart reservoir now retains up to 64 point-essential, pair-feasible states with at most ten holes, including equal-score states. Entries have distinct canonical block sets and differ by at least four blocks. Once full, a new entry replaces a member of the closest pair only if it increases that minimum distance. Three quarters of restarts draw from this reservoir; the remainder draw from the score frontier. This reservoir is distinct from the label-invariant fingerprint filter used to export nonisomorphic seeds.

A new soft energy term favors lower heavy-triple overlap: `max(0, 3*n6 + 4*n7 - 16) + 8*sum(max(0, multiplicity - 7))`, where `n6` and `n7` count triples of multiplicity six and seven. Its cyclic weights are 0, 2, 4, 6, 10, and 16. This is a search preference only; this experiment does not rely on a new global reduction or theorem.

The 300-second pilot used RNG seed 2026100341 and made 272,495,131 proposals. It retained 64 reservoir states after 181 insertions, with 110 of 136 restarts drawn from the reservoir. Of 13,503,347 valid four-to-eight-block proposals, only one four-block move was accepted; none of lengths five through eight was accepted. Five three-block cycles were accepted. No seven-hole point-essential pair-feasible state or complete cover was found. The nine search campaigns now total 1,020 seconds and 1,486,342,120 proposals.

The new useful seed has ten holes and heavy excess zero: its triple multiplicity histogram is `{0:10, 1:482, 2:63, 5:1, 6:1, 7:3}`. The four heavy triples are pairwise vertex-disjoint. This seed is `plateau-2026100341/pilot-heavy-e0-h10-u0-p0.txt`, with canonical SHA256 `22911cdeac8e4dddd29072763f3bab5c86201eea5698248d288a3a085233bb55`. It is a new search hint, not an improved hole count. The run reproduced the same seven eight-hole invariant classes.

## Verification and evidence

All 168 saved pilot, follow-up, cycle-control and sanitizer snapshots passed independent parsing, degree, pair and private-triple recounts: 118 original snapshots and 50 new snapshots. Both the package verifier and standalone checker agree on every missing-triple list and canonical hash. They reject all snapshots as incomplete covers. Ten focused damage, relabeling, heavy-score and long-cycle controls pass after the v1.2 changes. The full suite passed 212 tests, and Ruff passed. AddressSanitizer and UndefinedBehaviorSanitizer controls passed for all three C++ source versions; duplicate, malformed and damaged seed controls were rejected.

Evidence is under `experiments/2026-10-03/essential-regular-heuristic/`. `summary.json` records all budgets, seeds, source versions and run totals. `all-candidate-checks.json.gz` holds every candidate check. The useful original seven seeds are `diversity-2026100318-variant-{0..6}-h8-u0-p0.txt`; their exact hashes and fingerprints are in `diversity-seeds.json.gz`.

The v1.2 evidence is in the `plateau-2026100341/` subdirectory; its `candidate-checks.json.gz` preserves all 50 new independent checks. Its search log records move-size counts, accepted moves, restart counts, reservoir size, heavy-score improvements and long-cycle controls. The current search source is `scripts/essential_regular_heuristic.cpp`, with independent recount code in `scripts/verify_essential_heuristic.py`. Archived source versions and native binaries remain outside Git in `experiments/scratch/essential-regular-heuristic-20261003/`.
