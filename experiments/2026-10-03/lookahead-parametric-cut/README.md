```
Document:    Exact Parametric Cut for Regular Four-Sevenfold Heavy Blocks
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      acda98892a9a5cf011c7aa43534b63d8d9aa73c0fcd146a07cdf6af763c2dda8
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Reusable heavy-block cut

The checked rational dual gives this necessary inequality:

**sum(c_b * h_b) >= 108686.**

Here `h_b` is the indicator of one of the 276 legal heavy blocks. The signed
integer coefficients `c_b`, block labels and original zero-based global block
IDs are saved together in `cut.json`. Blocks are in original lexicographic
order. Point labels remain 1-based. Coefficients range from -6073 to 10764.
The source dual's denominator is 1000; the displayed integer inequality is
already scaled and needs no division during evaluation.

The ten-hole tuple has left-hand side 98144. It violates the inequality by
10542, equivalent to the independently checked rational gap 5271/500. This
excludes completion of that heavy tuple within the stated family. It does not
exclude a first-link representative or give a global covering lower bound.

## Exact scope and complete block sets

The four anchors are {1,2,3}, {5,6,7}, {9,10,11} and {13,14,15}, with own hubs
4, 8, 12 and 16. The family has 64 distinct blocks, full triple coverage, point
degree 20, and seven heavy blocks for each anchor. In each anchor template,
every external point occurs once except its own hub, which occurs twice.
No particular graph of pairs among the hubs is selected.

The proved pair identities force the pair inside each anchor to occur seven
times, its own anchor-point/hub pair six times, and all other pairs touching an
anchor point five times. A heavy block consists of an anchor plus an external
edge. That edge cannot be a pair inside another anchor: that pair's own seven
heavy blocks already attain its exact count seven. There are choose(13,2) - 9
= 69 permitted external edges per anchor and 276 heavy candidates altogether.
The checker generates them independently anchor by anchor. Every ordinary
block contains at most one point from each anchor; all 1200 such blocks remain.

For each hub, the three hub-pair counts sum to 17 and each is at least five.
Their excesses above five form a degree-two multigraph on four vertices. There
are exactly six possibilities: three four-cycles and three doubled matchings.
Every hub-pair count is therefore at most seven. Every nonheavy triple either
has fixed incidence one or two because it contains an anchor pair, or contains
a pair occurring five times under each of these six graphs. Such a pair has
only one repeated triple incidence, so that triple occurs at most twice. The
checker replays this classification for all 556 nonheavy triples.

These restrictions preserve complete covers in this regular four-sevenfold
family. The cut is not asserted for arbitrary selections of 276 heavy blocks
that fail the family conditions, for nonregular covers, or for other anchor
and hub labelings without a corresponding relabeling.

## Parametric derivation

Let x index all 1200 ordinary variables in [0,1], and let h index the 276
heavy indicators. For each source row r, write the bounds as

    l_r - D_r h <= A_r x <= u_r - D_r h.

`row-map.json` records all 697 rows in their audited order: cardinality, 560
triples, 16 points and 120 pairs. Each D_r is the incidence vector of heavy
blocks containing that row's subset. The cardinality row uses the empty subset,
contained in every block, so its constant is 64, not the seed-specific 36.
Point constants are 20. Triple lower constants are one; nonheavy triple upper
constants are two, and heavy triples have no finite upper bound. Anchor pair
constants are their exact counts; hub pair bounds are five and seven.

For each saved signed dual weight w_r, choose the lower constant when w_r is
positive and the upper constant when w_r is negative. Negative weights on an
unbounded upper row are rejected. Let

    K = sum_r w_r * chosen_constant_r,
    a_j = sum_r w_r * A_rj,
    c_b = sum_r w_r * D_rb.

Then every feasible completion satisfies

    sum_j a_j x_j >= K - sum_b c_b h_b.

Because each x_j lies in [0,1], the left-hand side is at most
M = sum_j max(0, a_j). The saved weights give K = 108773 and M = 87. Therefore
sum_b c_b h_b >= K - M = 108686. This argument holds simultaneously for all
valid heavy tuples in the family and all six hub graphs. It does not rely on
the seed-specific heavy counts when constructing the coefficient vector.

## Replay and controls

`derive.py` generates the symbolic row map and coefficient artifact from the
frozen dual. `check.py` is a separate pure-Python checker: it imports no solver,
model builder or derivation code. It independently regenerates all ordinary and
heavy blocks, reconstructs each combined coefficient by summing the block's
point, pair and triple weights, checks every constant and bound, and replays the
exact seed contradiction using rational arithmetic. Source model, dual, root
audit, checker and artifact hashes are bound in the saved records.

Fifteen altered controls are rejected, covering the inequality direction,
threshold, denominator, constants, heavy coefficients, heavy and ordinary IDs,
ordinary combined coefficients, missing heavy candidates, seed fields,
duplicate dual rows and changed dual weights. `audit.json` records the result.
No solver was launched to derive or check this cut.

Run from the repository root:

    uv run python experiments/2026-10-03/lookahead-parametric-cut/check.py

For constructive search, sum the seven coefficients in each selected anchor
template and add the four template scores. A total below 108686 rules out that
heavy tuple in this family; a total at or above the threshold only passes this
one necessary condition. A small table of per-template scores can therefore
screen or steer template moves without solving the ordinary completion again.
The cut does not by itself produce a covering witness.
