```text
Document:    Counting Consequences of Zero Stronger Pair Deficit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      7acabacc5d475a54751a97fac1573c5d9fa5891bc230680e3ea9c1cf62aa7f07
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Counting consequences of zero stronger pair deficit

Let F be a family of 64 distinct five-blocks on 16 points. Write lambda(uv) for the number of blocks containing pair uv, mu(uvw) for triple multiplicity, and r(u) for point replication. For a fixed pair uv, let c_1 >= ... >= c_14 be its third-point triple counts. Counting incidences gives sum(c_i)=3 lambda(uv).

The active independent oracle uses `max(0, 12 - 3*r + triples[a] + triples[b])` at line 63, adds each pair's maximum at line 66, and adds all expanded rows at line 67. Here the local variable `r` means pair multiplicity lambda, not point replication. Thus D2max=0 is equivalent to every pair satisfying

```
c_1 + c_2 <= 3 lambda(uv) - 12.
```

All terms are nonnegative, so D2max=0 and D2sum=0 are equivalent zero conditions. The source is `experiments/2026-10-04/weak-pair-swap-scan-independent/oracle.py`, lines 41-91, SHA256 `7fc14c0e2078894a03cc8945c94cb8f9987e79f4780d49558d311e83f0d0ba92`. The total-count identity is checked at line 56.

## Pairs of multiplicity five have no missing third point

Assume all-pairs D2max=0. Every pair has lambda>=5. For lambda<=3 the displayed right side is negative, which is impossible. For lambda=4 it forces all third-point counts to zero, contradicting their sum of 12.

At lambda=5 the top two counts sum to at most three, while all 14 counts sum to 15. If c_1<=1, their sum is at most 14. If c_1>=3, then c_2=0 and c_1<=3, giving total at most three. Therefore c_1=2, every other count is at most one, and total 15 forces exactly

```
(2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1).
```

Every triple through that pair is covered. Consequently, if a triple is missing under all-pairs D2max=0, all three of its pairs must have multiplicity at least six.

## A replication-19 point has a complete pair-covering link

There are 120 pairs, and each five-block contributes ten pair incidences. Hence

```
sum_over_pairs (lambda(uv)-5) = 64*10 - 120*5 = 40.
```

All these excesses are nonnegative under the zero-deficit assumption. At a point u, each incident block contributes four pairs, so

```
sum_over_v_not_u (lambda(uv)-5) = 4*r(u) - 15*5.
```

If r(u)=19, this sum equals one: exactly one incident pair has multiplicity six and the other fourteen have multiplicity five. A missing triple containing u would require two incident pairs with positive excess, which is impossible. Thus every triple containing u is covered. Equivalently, deleting u from its 19 incident five-blocks gives a 19-block family of four-subsets covering all 105 pairs on the other 15 points: a complete C(15,4,2) link. This conclusion uses all-pairs D2max=0 and the exact incidence counts; it does not assume global triple coverage.

## Limits of these deductions

A full triple cover implies D2max=0: after removing any two third-point counts, the remaining twelve counts are each at least one. The converse for a 64-block global family is not proved here.

For a single pair, lambda=6 with third-point counts consisting of nine twos and five zeros has sum 18 and top-two sum four, which satisfies the permitted bound six despite local missing third points. This is only a local count example against single-pair sufficiency. It is not a constructed 64-block global counterexample to all-pairs D2max=0 implying coverage.

These necessary consequences may guide a bounded D2-first experiment. They are not a solution of C(16,5,3), a global lower bound, or an equivalence between zero D2 and full coverage. No optimizer or native search was run for this note.
