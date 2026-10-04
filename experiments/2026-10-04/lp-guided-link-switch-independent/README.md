```
Document:    Independent Gate and Readback for LP-Guided Two-Edge Switches
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      2c4a1b7f175efd19c94107ae40c94b1ea60b1e79da1586301d851e3b314cbe6b
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent link-switch preparation gate

The frozen generator and proposal passed a separate finite review with no LP
or optimization calls. The reviewer independently enumerates every pair of
simple replacement edges on the original endpoint multiset with the same
vertex degrees. This differs from the generator's two explicit reconnection
formulas and checks completeness of the declared one-link, two-edge neighborhood.

The same 132 distinct heavy tuples result: 34 for each of anchors {1,2,3} and
{5,6,7}, and 32 for each of {9,10,11} and {13,14,15}. Every tuple has 28 heavy
blocks from the same 276-block universe, seven blocks per anchor, outside-point
incidences two at its own hub and one at each other outside point, and no
nonanchor heavy triple above multiplicity two.

The checker reconstructs all 697 constant/support rows directly from blocks,
triples, points and pairs. The original model and all 132 neighbor row sets
match these direct counts and the generator's finite-bound shifts. All 1,200
ordinary and 276 heavy column IDs remain in the original global lexicographic
ordering. Row and heavy-tuple hashes use compact JSON with no newline, as
specified by this proposal; this differs from earlier text-based heavy hashes.

All fourteen cut dot products, positive violations, tie-break ordering and the
first twenty selected ranks replay exactly. Each source signed dual has
maximum absolute row weight 1000, so its positive cut gap divided by 1000 is a
valid lower bound on the ordinary LP's L1 elastic objective. The first-round
selected lower bounds range from 2.703 to 5.927. These are lower bounds for
ranking, not solved LP objectives or feasibility decisions.

`audit.json` binds the frozen generator, proposal, checked bundle and this
checker. The gate validates the proposed preparation and its 3-round,
60-evaluation, 30-solver-second bounds; it does not execute the runner or certify
any later pilot outcome. The mathematical family/basis and cut proofs were
already independently audited. The scope remains a local finite neighborhood,
with no unrestricted covering claim or first-link registry change.

## Completed pilot readback

`readback.py` replays all three rank lists, 401 candidate row sets, all sixty
saved numerical vectors, chosen best records and the recorded solver budget.
It verifies final elastic objective 5.575882992498541 and produces an exact
rational residual upper bound below 5.575883 without any new solver call.
The final pattern passes the old fourteen cuts but is not certified feasible
by this readback. See `readback.json`.

The selected 28 heavy blocks combined with the original 36 ordinary blocks
form `selected-binding-seed.txt`, which a subsequent fresh diagnostic verifies
as a five-hole near-cover with both cover checkers. The full diagnostic, exact
5.425-gap obstruction and new reusable cut are in `../lp-guided-best-lp/`.
