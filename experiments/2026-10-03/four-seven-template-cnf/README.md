```text
Document:    Restricted Boolean Template CP to Proof CNF Equivalence
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      a48f63b963b4d00a90d5a287acf4e92466ee3300b7470d7d664cea337e6a9d58
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Restricted CP to proof CNF translation

This new experiment translates only the already audited matching-029/(m4,z)=(0,2) and matching-063/(0,1) Boolean CP models. The first 55,528 DIMACS variables keep the original CP order, with CP variable i mapped to DIMACS i+1. Every further variable is local circuit state. The 4,368 block variables remain first and lexicographic.

## Signed-row equivalence

For each coefficient a and Boolean x, positive a contributes a repeated copies of literal x. Negative a contributes -a repeated copies of literal not-x and the constant offset a. Thus the original weighted sum equals the unweighted literal count plus the sum of negative coefficients. The translator subtracts that exact offset from both bounds, then intersects with the possible count interval [0,n]. A weight of four repeats the identical literal four times; it creates no independent aliases.

If useful, all literals are complemented and [L,U] becomes [n-U,n-L]. This is an exact count identity. Empty or full intervals become contradiction, tautology or unit clauses. At-least-one becomes one clause.

## Threshold circuit proof

For remaining intervals, q(i,j) means at least j of the first i literal occurrences are true. Base values are q(i,0)=true and q(i,j)=false when j>i. Each allocated threshold obeys

q(i,j) iff a OR (x AND b), where a=q(i-1,j), b=q(i-1,j-1), x is occurrence i.

The four clauses are (not-a OR q), (not-x OR not-b OR q), (not-q OR a OR x), and (not-q OR a OR b). Clauses containing the Boolean constant true are omitted; false constants are removed. Integer literal repetition and complementary integer literals are preserved. These clauses are exactly the two implications of the stated equivalence, even when input literals repeat or share underlying variables.

Induction on i proves every q equals its intended prefix threshold in any satisfying assignment. Conversely, assigning actual prefix threshold values satisfies every circuit clause for any original Boolean assignment. Requiring q(n,L) and not-q(n,U+1), whenever the corresponding bound is active, therefore gives both directions of the exact row projection. Only thresholds needed by these bounds are built.

At-most-one uses a linear Sinz chain. Its implications force each prefix state when an earlier occurrence is true and forbid any later occurrence from also being true. If at most one occurrence is true, assigning prefix states to their actual OR satisfies the chain. Adding the at-least-one clause yields exact one. This argument also permits repeated or complemented input occurrences.

Each row gets fresh auxiliary variables, so the per-row extensions combine without coupling. All original variables are Boolean, and the restricted protos have no objective, reified constraints or other semantic fields. Consequently projection of the CNF satisfying assignments equals exactly the source restricted CP assignments. This is not an unrestricted covering encoding.

## Frozen outputs and proof gate

The matching-029 CNF has 1,116,193 variables and 3,766,434 clauses (76,410,492 bytes). The matching-063 CNF has 1,115,887 variables and 3,765,211 clauses (76,381,525 bytes). `manifest.json` binds both source models, the prior independent model audit, builder, DIMACS files and compressed per-row traces. Each trace records source-row hash, exact offset, normalized interval/hash, circuit recipe and clause/auxiliary ranges.

Large DIMACS, row traces, source checkouts and eventual proof artifacts remain in ignored scratch. An independent translation audit is required before a bounded proof run. A solver UNSAT result remains provisional until the exact frozen DIMACS/proof pair passes a separate checker. No new exclusion or global lower bound is claimed by preparing these files.
