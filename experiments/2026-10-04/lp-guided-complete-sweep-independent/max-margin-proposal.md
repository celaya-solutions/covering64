```text
Document:    Maximum Normalized Cut Margin Proposal
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      77e300ad31e4b2a675370b45d5de632c86defa82b0829fb443a342429195cc49
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

The completed nearest-heavy campaign added 95 checked cuts to the initial 238.
The independent intersection checker reconstructs all 333 planes from signed
row weights and verifies every maximum absolute row weight equals its certified
denominator. The denominators are 1,000 and 1,000,000. All 27 finite neighbors
left unresolved by the 113-plane envelope are now excluded. No candidate from
that fallback needs another LP solve.

The proposed next search keeps the same structural heavy family and 333 exact
necessary cuts, but replaces nearest-heavy distance with maximum normalized
margin inside those cuts. It does not use Hamming distance as an objective or
restrict candidates to the preceding neighborhoods.

For cut k, write b_k·h >= rhs_k with denominator D_k. Its signed elastic lower
bound is (rhs_k - b_k·h)/D_k. Choose S = 1,000,000 and integer scaled values
a_k = (S/D_k)b_k and r_k = (S/D_k)rhs_k. Add an integer variable Z and solve:

    maximize Z
    Z >= 0
    Z <= a_k·h - r_k, for every checked cut k
    h satisfies the existing structural heavy master

This minimizes the maximum signed cut lower bound. It must use the signed
envelope without clamping to zero: every candidate satisfying all necessary
cuts has zero after clamping, which would erase the objective. The margin is
measured in millionths of elastic L1 slack. A large margin can indicate a new
region missed by the known cuts, but it does not establish a small actual LP
residual. The ordinary completion LP must measure that residual separately.

Since exactly 28 heavy blocks are selected, an exact safe upper bound is

    U = min_k(sum(the 28 largest entries of a_k) - r_k) = 141507155.

The largest absolute scaled coefficient is 17,579,998 and the largest absolute
scaled right-hand side is 138,999,389. Including U, the largest conservative
sum of absolute constraint activity is 1,965,950,222, well within signed 64-bit
integer arithmetic. These are finite arithmetic checks; no optimization was
used to obtain them. The new master would have 277 variables. Existing cut
inequalities can remain, or the margin inequalities with Z >= 0 imply them.

A suggested first budget is 20 candidates, at most three seconds per master
and one second per completion LP, with 80 combined solver seconds and 100 wall
seconds. Each iteration should save the master, parameters, logs, response,
exact achieved margin, objective bound, full primal/dual vectors, row hashes,
actual residual, and independently checked learned cut. Record FEASIBLE versus
OPTIMAL accurately; a feasible incumbent does not prove best possible margin.

Each new cut should use weights clipped to [-D,D], with negative weights zeroed
on infinite-upper rows, before exact column sums are formed. This retains a
valid normalized elastic bound even if numerical dual values have tiny norm
excursions. A positive exact source gap excludes the current tuple, giving
distinct candidates without arbitrary no-good exclusions. An unresolved
certificate or timeout is inconclusive and should be recorded as such.

This is a proposal only. No new master runner or solver call was made for it.
It supplies no unrestricted covering-number lower bound.
