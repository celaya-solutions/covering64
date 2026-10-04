```
Document:    Top-Two Pair Deficit Proof and Independent Controls
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      23ec32fcd8e07b644b7987c1cb05e9ed886689f51f22116adb7b46230800899c
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Top-two pair deficit proof and independent controls

For each pair P, let p=c(P), and let the 14 values z_x=c(P union {x}) be indexed by the distinct points outside P. Let m1 and m2 be the two largest positions. Their values may be equal. Define

```
d(P)   = max(0, 12 - 3*p + m1 + m2)
D2max  = sum_P d(P)
D2sum  = sum_P sum_{a<b outside P} max(0, 12 - 3*p + z_a + z_b)
```

## Exact zero equivalence, including ties

Every distinct-position sum z_a+z_b is at most m1+m2. The two maximizing positions are themselves one of the 91 pairs, including when their values tie. Adding the common constant and taking the positive part preserves this maximum. Thus d(P) is exactly the largest of the 91 strong-row deficits. Consequently

```
D2max = 0  iff  all 10,920 strong rows hold  iff  D2sum = 0
0 <= D2max <= D2sum <= 91*D2max.
```

Positive scores generally differ. Using distinct values instead of distinct positions is wrong. Using the same maximum position twice is also wrong.

## Consequences for actual five-point block families

Each selected block through P contributes to exactly three triple positions. Thus sum_x z_x=3*p and 0<=z_x<=p. If p>0, at least three positions are positive.

If d(P)=0, then m1+m2<=3*p-12. Counts p<=3 give a negative right side and are impossible. At p=4, the right side is zero, while the total triple mass is 12. Therefore p>=5. In particular m2>=1, so every z_x<=m1<=3*p-13. All single-triple deficits D3 are therefore zero. This proof has no incidence-regularity assumption.

There is also a real-valued implication for D3. Fix a position a and sum the 13 strong rows involving a. Their left side is

```
13*(3*p) - 13*z_a - sum_{b != a} z_b = 36*p - 12*z_a.
```

The summed right side is 156. Hence z_a<=3*p-13 whenever the exact mass identity holds, even before integrality. This linear combination proves redundancy of the single-triple rows in that relaxation; it does not audit any new solver encoding.

Zero D2max is a necessary-condition screen. It alone is not a verified cover, a global lower bound, or an infeasibility certificate. Every proposed cover still requires both verifiers.

## Independent finite controls

The audit source imports no optimizer or production metric helper. It checks all 47,905 triples (p,m1,m2) with p from 0 through 64 and 0<=m2<=m1<=p. Exactly 31,521 satisfy the necessary and sufficient abstract profile condition m1+m2<=3*p<=m1+13*m2. A full 14-entry vector is constructed for every such extremal profile and all 91 deficits are checked. These vectors need not all be realizable block links; the proof applies to the larger abstract count class. Of those profiles, 31,453 have zero maximum deficit, and every one satisfies the pair-floor and D3 implications.

Tie controls cover all 16,384 position masks at six positive heights, for 98,304 profiles. Another 116,280 histograms from eight boundary count values are checked in sorted, reversed, and rotated orders, for 348,840 orders. Finite controls support the implementation-independent algebra above; they are not an exhaustive enumeration of all block families.

Four damaged interpretations are rejected: deduplicating tied values, reusing one position twice, equating positive D2max with D2sum, and omitting the actual-family mass identity. Three explicit five-block pair links realize the tie, unique-maximum, and unequal-positive-score controls. They are small arithmetic controls, not 64-block candidates.

## Saved-state recount

The independently generated inventory in `../native-d2-readonly-inventory/result.json` lists every pair, all 14 distinct triple positions, and all violating rows. Its source and result hashes are bound in this receipt. Its three 64-block input families are bound to the previously passed native postcheck. A separate direct recount during this audit agreed with all three totals.

| State | Holes | D3 | D4 | D2max | D2sum | Violating pairs | Violating rows |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| H6 | 6 | 4 | 0 | 14 | 62 | 14 | 62 |
| H48 | 48 | 0 | 0 | 75 | 175 | 75 | 175 |
| H49 | 49 | 0 | 0 | 74 | 170 | 74 | 170 |

All positive strong-row deficits in these three states are one. Neither H48 nor H49 qualifies under D2max=0. All three remain noncovers. No production source or frozen experiment was changed, and no optimizer was called by this proof audit.
