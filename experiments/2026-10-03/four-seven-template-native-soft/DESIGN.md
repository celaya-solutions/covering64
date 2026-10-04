```text
Document:    Complete Heavy Template Soft-Score Pilot Design
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      25e913b1694e4baa98ea73b9ce1e0eda4ef2fe47a5a3dbfa2c02d052d762e980
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

This separate variant starts from the verified raw best states of native v1.0.
The matching seed has 21 uncovered triples; the cycle seed has 19. It preserves
v1.0, its full catalogs, and its four legal move families. Every full state has
64 distinct five-blocks and degree 20 at every point. It is a construction search
within a branch-derived family, with no completeness or connectivity claim.

The objective is `5 * holes + pair_target_L1 + 5 * nonheavy_excess`. The last term
is the sum of `max(0, triple_count - 2)` over all triples except the four complete
anchor triples. Every pair initially has target 5. Pairs within an anchor triple
have target 7; each anchor point with its own hub has target 6. For matching, hub
pairs (4,8) and (12,16) have target 7. For cycle, (4,8), (8,12), (12,16), and
(4,16) have target 6. These are soft penalties; they add no legal-move restriction.

The raw best minimizes holes, then score. The score best minimizes score, then
holes. Both records and their unique improvements are saved independently. Any
legal proposal reaching zero holes is accepted regardless of its score; the
process exits and the runner immediately invokes both covering checkers. Forced
controls and restart perturbations also stop upon finding zero holes. Nonzero
states remain failed candidates, even when their soft score improves.

The annealing temperature is five times v1.0:
`5 * (0.07 + 0.93 * (1 - phase)^3)`, with phase resetting every 100,000 proposals.
This preserves the previous temperature relative to a one-hole change after
weighting holes by five. Every 500,000 proposals, restart from the score best,
using the original seed every third restart, and attempt 50 perturbations.
Main-loop attempted/accepted counts exclude these restart perturbations and
include invalid main-loop attempts in the acceptance denominator.

Incremental pair and triple counts are checked against independent full native
recounts. Every applied move predicts its hole and score deltas before mutation
and checks the resulting totals. Four forced moves are saved before and after
application and after rollback; duplicate proposals must be rejected without
mutation. The Python auditor reconstructs pair targets and triple multiplicities,
checks every saved state's frozen catalog membership, and runs both covering
verifiers. Separate damaged-score controls alter each reported hole/score field.

Two 300-second pilots are authorized, one matching and one cycle, with at most
two single-thread native processes. They start only after the independent audit
gate. Complete logs, binary builds, verifier outputs, and state archives remain
under ignored `experiments/scratch/four-seven-template-native-v1.1.0/`.
