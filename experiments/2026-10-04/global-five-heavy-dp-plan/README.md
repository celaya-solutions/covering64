```
Document:    Global Five-Heavy DP Equivalence and Reachable-State Plan
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      30acf4994733326aeafddc34b42b9e3c5ed10f27a6ef530c5ea4b76cf3576432
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Global five-heavy DP: equivalence and reachable-state reduction

The existing five-heavy theorem says that a full 64-block cover cannot contain five pairwise-disjoint triples, all occurring at least six times, with at least two occurring seven or more times. Its degree-budget proof uses no incidence regularity or fixed labeling. This preparation encodes that necessary condition globally. It does not claim that satisfying the condition is sufficient for a covering, or prove an unrestricted lower bound.

## Exact weights and full recurrence

For each of the 560 triples T, use exact indicators s6(T) = [count(T) >= 6] and s7(T) = [count(T) >= 7]. Both implications are required for each threshold. Let w(T) = 5*s6(T) + s7(T), so its value is 0, 5, or 6. For five disjoint triples, a zero weight limits the sum to at most 24. If all five are heavy, the sum is 25 plus the number occurring at least seven times. Thus a sum above 26 is equivalent to the forbidden profile.

For any subset S of size divisible by three, let F(S) be the maximum weight sum over all partitions of S into triples, with F(empty) = 0. Every nonempty partition has exactly one triple T containing min(S). Therefore

F(S) = max over T contained in S, |T|=3, min(S) in T of (F(S minus T) + w(T)).

Introduce D(empty)=0 and, for every such transition, D(S) >= D(S minus T) + w(T). Use domains 0 <= D(S) <= 6*|S|/3 for sizes up to 12 and 0 <= D(S) <= 26 at size 15. The lower rows do not require every feasible D to equal F. Instead, induction proves every feasible D is at least F. Conversely, if each 15-point partition maximum is at most 26, choosing D=F satisfies every row and domain. Thus existence of D is exactly equivalent to excluding every forbidden five-triple partition. This argument also works with continuous D, though the prepared CP-SAT model uses bounded integers.

All sixteen 15-point subsets are included. Every five-disjoint-triple family is a partition of exactly one of them. Choosing the minimum point as pivot only picks a canonical recurrence decomposition; it imposes no condition on the selected blocks or point labels.

## Safe reachability reduction

Retain only states reached by starting at all sixteen size-15 targets and repeatedly deleting the triple containing the current minimum. After q deletions, every label in 1 through q must have been removed. Hence a retained state of size 3k excludes labels 1 through 5-k.

This condition is also sufficient. Given any size-3k state S excluding those q=5-k labels, use labels 1 through q as successive pivots. Outside S and these pivots there are exactly 2q+1 labels, all greater than q. Choose any 2q as companions, pair them with the pivots, and leave the final point unused. The union of S and those q triples is a 15-point target. Deleting its pivot triples in order reaches S. Therefore the closed-form state set is precisely the backward reachable set, not a heuristic subset. Every dependency of every retained row is retained, so the earlier induction and D=F construction remain valid.

| State size | Full states | Reachable states | Full rows | Reachable rows |
|---|---:|---:|---:|---:|
| 0 | 1 | 1 | 0 | 0 |
| 3 | 560 | 220 | 560 | 220 |
| 6 | 8,008 | 1,716 | 80,080 | 17,160 |
| 9 | 11,440 | 2,002 | 320,320 | 56,056 |
| 12 | 1,820 | 455 | 100,100 | 25,025 |
| 15 | 16 | 16 | 1,456 | 1,456 |
| Total | 21,845 | 4,410 | 502,516 | 99,917 |

Full state counts are binomial(16,3k). Reachable counts are binomial(11+k,3k), plus the empty state. Each nonempty state contributes binomial(3k-1,2) rows. Exact threshold channeling adds 1,120 Booleans and 2,240 half-reified rows; weight expressions are inlined, with no extra weight variables. Variable bounds encode the sixteen final caps directly.

## Independent finite controls and cost evidence

The saved check generates the full DAG, discovers the reachable DAG by backward traversal, and separately compares the result with the closed form. It writes complete packed relation tables under ignored scratch. It checks all 243 five-triple weight categories (217 allowed, 26 forbidden), exact threshold truth values for counts 0 through 78, and 2,028 subset/weight cases against direct unpruned combinations of triple IDs on up to nine points. Twelve weight vectors include all-zero, all-five, all-six, and nine seeded mixtures.

The full relation table has 2,010,064 coefficient occurrences when weights are inlined; the reachable table has 399,668. A triple's two indicators participate in at most 517 reachable recurrence rows, versus 2,731 full rows. The packed reachable relation table is 1,199,004 bytes. Uniform fixed-weight passes over the reachable DAG took about 0.013 seconds here; they measure arithmetic traversal only, not CP-SAT propagation, presolve, or search performance.

The inspected prior producers enforce two or three named partition cuts. They do not contain this global DP. The indexed-source search also found no existing global DP identifiers or max-equality recurrence. The new model retains the three named cuts and their exact indicators only to preserve the old model prefix for comparison; they are redundant under the global condition.

Actual propagation cost is uncertain. Partial block assignments can leave most threshold lower bounds at zero, while 99,917 extra linear rows still require storage and processing. Once four known heavy triples have total weight 21, the cap can imply the remaining disjoint triple has weight at most 5; at total 22 it must have weight zero. These are logical consequences, not measured solver performance. The separate prepared model records build time, memory, serialized size, and a complete least-value hint. Only one bounded 120-second, four-worker full-block run is planned after an independent gate, with seed 2026104104.
