```text
Document:    Forced Structure of a 61-Block C(16,5,3) Cover
Version:     v2.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-06
SHA256:      194d7eff4f8dfa6654cbb57a3577e74e54be3ddf5103a4fb522a73934fb034f8
Chain:       solana-mainnet
Tx:          2ThLQVG4BJCgu5Q1gSSCTBM26eNMJPPJDzd6SnpthKgrXS89fi3hEg6ou2Y9G8ybh9XsqfPjMYprkx5gZC6VB79s
License:     CC BY 4.0 / Celaya Solutions
```

# Forced structure of a 61-block cover

The recorded bounds are 61 <= C(16,5,3) <= 65. The program now works upward
from the lower bound: show that 61 blocks are impossible, then 62 and 63, and
finally 64. Each step would raise the lower bound and needs a complete,
independently checkable argument. This note proves the structure any 61-block
cover must have and then excludes such a cover, so C(16,5,3) >= 62.

## Lemmas

Write r_x for the number of blocks containing point x, lambda_xy for pairs and
mu_T for triples.

**Lemma 1.** Every pair lies in at least five blocks and every point in at
least nineteen. The blocks through {x,y} must meet all 14 other points, three
per block, so lambda_xy >= 5. Each block through x holds four pairs at x, so
4 r_x = sum_y lambda_xy >= 75 and r_x >= 19.

**Lemma 2.** A 61-block cover has one point z of degree 20 and fifteen points
of degree 19, because the degrees sum to 305 = 16 * 19 + 1.

**Lemma 3.** Let e_xy = lambda_xy - 5 >= 0. Then sum_y e_xy = 4 r_x - 75, which
is 1 at each degree-19 point and 5 at z. A degree-19 point therefore has one
partner with lambda = 6. The five units at z go to five distinct points A, and
the other ten points M pair off among themselves. So the pairs with
lambda = 6 form E = K(1,5) plus a perfect matching on M; every other pair has
lambda = 5. E is unique up to relabeling.

**Lemma 4.** For each pair, sum_w (mu_xyw - 1) = 3 lambda_xy - 14, which is 1
off E and 4 on E. A triple with mu >= 3 would put at least two units on each
of its pairs, so all three pairs would lie in E, which has no triangle. Hence
every triple is covered once or twice, each non-E pair lies in exactly one
doubled triple, each E pair in exactly four, and there are exactly 50 doubled
triples.

**Lemma 5.** Removing a degree-19 point v from its blocks leaves 19
quadruples covering all pairs on the other 15 points, a minimum C(15,4,2)
cover. Its point degrees are lambda_vw: 6 at v's partner p and 5 elsewhere.
Its pairs covered twice form a four-edge star at p plus a perfect matching of
the remaining ten points. By Allston, Buskens and Stanton (JCMCC 4, 1988),
independently reconstructed in `experiments/2026-10-03/link-classification/`,
such covers fall into exactly four isomorphism classes. In each class one of
the six quadruples through p contains three of the four star leaves; a direct
check of the four representatives confirms this.

**Lemma 6.** The doubled triples through z form a graph X_z on A and M with
degree 4 at each point of A and degree 1 at each point of M. If X_z has n_2
edges inside A, then n_2 lies between 5 and 10, with 20 - 2 n_2 edges between
A and M and n_2 - 5 edges inside M. Further pair counts are consistent and do
not by themselves exclude the structure.

Thus a 61-block cover exists exactly when there is a set of 61 blocks in which
every triple is covered once or twice, each non-E pair lies in exactly one
doubled triple and each E pair in exactly four, with E as in Lemma 3.

## Exclusion of 61 blocks

Take any A-point a. Its partner is z, so by Lemma 5 its link is one of the four
classified covers with z as its center. Relabel the points so that a = 1 and the
link equals one of the representatives in
`experiments/2026-10-03/link-classification/`, with z = 2. What remains unknown
is which four of the points 3..16 are the other points of A, and the perfect
matching of pairs with multiplicity six on the other ten points.

For each of the four representatives, a CNF with 144,553 variables and 512,424
clauses states only necessary conditions: the 19 blocks through point 1 are
the link blocks, every triple is covered once or twice, each pair outside E lies
in exactly one doubled triple and each pair in E in exactly four, and E is the
five-edge star at 2 (containing 1-2) plus a perfect matching of the remaining
ten points, encoded with variables. All four CNFs are unsatisfiable:

- Lingeling refutations with DRAT proofs (13.0 to 15.6 million lines), all
  accepted by drat-trim (`experiments/2026-10-05/lb61-certified/`);
- CaDiCaL 1.9.5 UNSAT on the same encoder (`experiments/2026-10-05/lb61-fixed-link-sat/`);
- an independently written CP-SAT model, INFEASIBLE in all four cases
  (`experiments/2026-10-05/lb61-crosscheck/`).

Hence no 61-block cover exists and **C(16,5,3) >= 62**. The argument relies on
the published four-class classification of minimum C(15,4,2) covers (Allston,
Buskens and Stanton, 1988), reconstructed independently in this repository.

Earlier exploratory probes, all inconclusive, are recorded in
`experiments/2026-10-05/lower-bound-61-probes/`.
