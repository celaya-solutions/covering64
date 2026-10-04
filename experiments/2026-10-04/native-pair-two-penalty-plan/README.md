```text
Document:    Stronger Native Pair Penalty Read-Only Plan
Version:     v1.2.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      e4cf452cc7fd4324f13bf8609c084b09c659ff9cb5455301b218ca2de260ebe8
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```
# Proposed stronger pair-penalty pilot

This plan now records root approval to implement the isolated phase-1 pilot. No optimizer may run before its fresh independent gate and GO. The next target is a 64-block partial family that satisfies every stronger pair-two-triple row. Such a family would be a feasible starting point for the stronger compact count model while it may still leave triples uncovered.

For each pair P, list the exact counts of all 14 triples P+x. Let a and b be the largest two values from different triple positions, allowing a=b. Define d(P)=max(0,12-3c(P)+a+b), and D2max=sum d(P) over the 120 pairs. The maximum pairwise sum over distinct positions is a+b; therefore d(P) is the maximum of the pair's 91 explicit row deficits, and D2max=0 is equivalent to satisfying all 10,920 stronger rows. This aggregate is not their total deficit sum. The independent top-two audit and manifest are frozen: audit SHA256 `796bf612ebe939bad5d346c3ac4348ab77b072c12c987f35b5e09647fef64e22`, manifest SHA256 `117a3260f137fd45cded1757b1b20cab0541b647bcb896ed55329cebb959a2c2`. They establish zero equivalence, pair minimum at least 5 and D3=0 for exact family counts. The existing stronger-row audit establishes D4 dominance.

Both proposed starts pass the audited all-relabel cap-55 screen for the original core, plus all four explicitly checked core caps. Their zero D3/D4 status does not make them legal for the stronger rows:

| Seed | Start holes | D2max | Full row deficit sum | Four named core overlaps |
| --- | ---: | ---: | ---: | --- |
| 2026104501 | 48 | 75 | 175 | 0, 1, 1, 12 |
| 2026104502 | 49 | 74 | 170 | 0, 2, 2, 4 |

Every violated pair in these starts has compact deficit 1. The runs keep distinct assigned starts. If the first run reaches zero D2max, the entire pilot stops and the second seed is skipped; otherwise the second keeps its assigned hint. No time is reallocated. All 64 slots and all 4,368 blocks remain available. The only initial hard restrictions are distinctness/cardinality and the four audited core caps of 55. There is no fixed degree, hard pair floor, radius limit or all-relabel hard guard.

## Recommended objective and phases

Use integer energy E=20*D2max+H for phase-A Metropolis acceptance, while ranking best states and restart states lexicographically by (D2max,H), retaining the first tie. These are different roles: the weighted energy is not globally lexicographic. However, one block replacement changes H by at most 10, so a one-unit reduction in D2max always reduces E even if holes increase maximally. Lexicographic records prevent a much lower-hole state with worse D2max from replacing a better primary-target restart.

For phase A, divide the integer energy difference by 20 and retain the prior numerical temperature schedule: T=0.06+(0.7+0.1*(restart mod 4))*(1-step/1,500,000)^3. A D2max unit therefore costs one annealing unit and a hole costs 0.05 units. Every third restart uses the assigned original hint; other restarts use the best lexicographic state. Restart spans remain 1,500,000 proposals for this initial pilot. No global-profile term is added to the proposed energy; profile status remains a diagnostic on every saved state.

Stop each native run immediately on its first fully recounted D2max=0 state. For H>0, save the state and emit `qualified_hint_found`; it remains an incomplete family. For H=0, save a candidate cover and require both existing verifiers before claiming a cover. There is no second optimization phase or added budget in this pilot. The compact CP model may use a qualified hint later under separate authorization. Global-profile status is independently recounted and reported, without adding an unapproved energy term or hard guard.

The strongest alternative is a fully lexicographic scalar such as 561*D2max+H, since 0<=H<=560, or a greedy lexicographic acceptance rule. The former changes hole-to-deficit temperature scaling markedly; the latter can block useful uphill escapes. The recommended weight 20 plus lexicographic records gives strict single-move priority while preserving controlled annealing. Root approved weight 20 and lexicographic best/restart records for phase 1 only; the fresh execution gate is still required.

## Implementation and verification gate

A proposed move affects the union of pairs in its removed and added blocks, including shared pairs with unchanged pair counts. Any changed triple lies in one of those blocks, so every affected row-pair is in the union. Recomputing the largest two counts over 14 positions for at most 20 pairs needs at most 280 position inspections. The proposed energy needs pair counts and the existing triple counts; it does not need a quad-count cache. D3, D4 and the full stronger-row sum should still be independently recounted for saved states and periodic audits. The independent proof now permits omission of separate D3/D4 penalties and hard pair-floor guards, while saved-state recounts retain those metrics.

Keep separate best-primary, raw-hole diagnostic, legal-hole and current records. A legal-hole record may be absent. Require both existing covering verifiers for every saved family and a separate complete count-row check. Zero D2max with positive H must be labeled a partial family, never a cover. Save current and all best roles through ordinary, interrupted, qualified-hint and cover-found exits.

Controls must compare every compact per-pair value with all 91 explicit row deficits, especially equal maxima at different positions, zero-valued positions and count permutations. Check all replacement intersection sizes, zero-net-change shared pairs, energy and rollback, all four cap boundaries, first-zero stop decisions and restart sources, malformed controls, and common final metadata. Run ASan/UBSan, then freeze source, binary, compiler, inputs, settings, controls and recorder. Require a fresh independent gate before any optimizer call.

The approved pilot allows at most two sequential calls of at most 60 seconds each with seeds 2026104501 and 2026104502, watchdog 75 seconds, termination grace 5 seconds, and no relaunch or extension. Finding a qualified hint ends that native call and the entire pilot immediately; the recorder saves the actual call count and any skipped-seed reason. Preserve every record, both verifier receipts, source hashes and full logs. Root approved weight 20, lexicographic best/restart records, four caps, and phase 1 only. Freeze the new source, controls and execution manifest, then obtain the independent gate and GO before starting either seed.
