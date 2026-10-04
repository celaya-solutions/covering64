```
Document:    Second Exact Parametric Cut for Regular Heavy Blocks
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      5cc9caf9ad63f45b3ea3de5d48931178a773c86a6a8f2e7e8980336a5f1fd404
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Second reusable heavy-block cut

The checked new dual yields the necessary integer inequality

    sum(c2_b * h_b) >= 104444.

The 276 signed coefficients, heavy blocks and original global block IDs are
stored in cut.json. Heavy indicators and ordinary variables retain lexicographic
order, with 1-based point labels. The source rational denominator is 1000; the
integer inequality is already scaled. Coefficients range from -6728 to 11645.
The cut-pilot heavy tuple scores 91904 and violates the bound by 12540, equal
to the exact rational gap 627/50. Its previous-cut orbit had no violation, so
this second certificate adds information for that tuple.

## Exact scope

This is conditional on the regular degree-20 four-sevenfold family with anchors
{1,2,3}, {5,6,7}, {9,10,11}, {13,14,15} and own hubs 4,8,12,16. Each anchor has
seven heavy blocks whose external edges cover every outside point once except
its own hub twice. Each heavy block's external edge avoids an internal pair of
another anchor, giving all 69 legal heavy candidates per group and 276 total.
All 1200 ordinary blocks remain available. All six possible hub graphs remain
allowed. No first-link registry exclusion is used to derive this cut.

The proved anchor-pair identities, hub-pair bounds five through seven and upper
bound two on nonheavy triples are the same previously checked consequences of
coverage and degree 20. The standalone checker replays their six-graph finite
classification. The inequality is not asserted for unrestricted covering models,
other anchor/hub assignments without corresponding relabeling, or heavy tuples
that do not satisfy this regular family. No global bound or first-link exclusion
is claimed.

## Parametric derivation and independent replay

The source model has 697 rows. For each row r, its heavy dependence is

    l_r - D_r h <= A_r x <= u_r - D_r h.

The symbolic row map records the constant bounds and incidence subsets for the
cardinality row, 560 triples, 16 points and 120 pairs. In particular, cardinality
uses constant 64 and subtracts all heavy indicators; it does not hard-code the
seed-specific ordinary count 36 in the reusable cut.

For signed multiplier w_r, use the lower constant for a positive weight and
the upper constant for a negative weight. Negative weights on infinite upper
bounds are rejected. The 542 nonzero multipliers give

    K = sum_r w_r * selected_constant_r = 104552,
    a_j = sum_r w_r * A_rj,
    c2_b = sum_r w_r * D_rb.

Every feasible completion obeys sum(a_j*x_j) >= K - sum(c2_b*h_b). The ordinary
box x in [0,1] gives sum(a_j*x_j) <= sum(max(0,a_j)) = 108. Subtracting this
box maximum proves the threshold 104444, simultaneously for every valid heavy
tuple in this family and every hub graph.

Root separately replayed the source fixed-tuple dual before this derivation;
its receipt is ../cut-pilot-heavy-completion-independent/dual-audit.json.
`derive.py` generates row-map.json and cut.json. `check.py` imports no solver,
model builder or deriver. It reconstructs every block coefficient from its
point, pair and triple weights, verifies all constants, checks the complete
276-heavy and 1200-ordinary inventories and replays the exact seed contradiction.
Fifteen damaged controls are rejected. Source/model/dual/gate hashes and the
result are saved in audit.json. No solver or native change was made here.

Run the standalone replay from the repository root:

    uv run python experiments/2026-10-03/cut-pilot-parametric-cut/check.py
