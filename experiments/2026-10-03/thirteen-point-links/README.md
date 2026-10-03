```
Document:    Thirteen-point local family evidence and determinant obstruction
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      7b937fadab47f59ccd1fcee4f6735b092f3ab54b8c8b0b247de9d449b3cee67e
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions```

# Thirteen-point local families in the multiplicity-seven branch

These results concern 13 distinct quadruples on 13 points, each point occurring four times, covering every pair outside G=P3 union5K2. Point 1 is the star center and points 2 and 3 are its leaves. Explicitly, G consists of {1,2}, {1,3}, {4,5}, {6,7}, {8,9}, {10,11}, {12,13}.

## A nonplane family exists

`spoke-counterexample.txt` is an explicit 13-block, degree-four family whose missing pairs are {1,2}, {4,5}, {6,7}, {8,9}, {10,11}, {12,13}. It covers {1,3}. Both package and standalone verifiers agree on all six holes and its canonical hash. The family is therefore a valid local family but is not a projective plane and is not a complete pair covering.

The bounded CP search found it in 10.2301 seconds, using seed 2026100331, two workers, a 30-second budget and OR-Tools 9.15.6755. Its full result is retained here; the exact source and solver log remain under `experiments/scratch/thirteen-point-rigidity-20261003/`. The witness disproves the proposed local projective-plane uniqueness assumption.

A separate attempt to force both star spokes missing returned UNKNOWN after 30.005459 seconds. That solver result is inconclusive. The exact determinant argument below is separate from it.

## Finite determinant obstruction for both missing spokes

Let A be the 13 by13 point-block incidence matrix of such a family. Every row and column sums to four. Let H be its missing-pair graph and F its positive pair-excess multigraph. Since each point is in four quadruples, it has exactly 12 pair incidences, so the F degree and H degree agree at every vertex. Their edge supports are disjoint, and H is a subgraph of G.

If both star spokes are missing, H is isomorphic to P3 union mK2 for some m from zero through five. There is exactly one possible vertex of degree two; all other nonisolated vertices have degree one. Consequently F is simple: an edge of multiplicity two would require two vertices with degree at least two.

For each m, fix H={1,2},{1,3} together with the first m matching edges. The hub's two F-neighbors must be chosen among the 2m matching vertices, because F cannot use either negative spoke. Once those two neighbors are chosen, the remaining degree-one vertices must be paired. Exhaust all perfect matchings and reject those using an edge of H. This lists every possible F exactly once. Fixing the first m matching edges loses no case, because permuting the five matching components of G is an isomorphism.

The Gram matrix AAᵀ has diagonal four and off-diagonal entries 1+F-H. Its determinant must be the integer square det(A)^2. The stdlib checker computes every determinant by exact fraction-free elimination; no floating-point arithmetic or solver conclusion is used.

| Matching edges m | Positive excess graphs checked |
| --- | ---: |
| 0 | 0 |
| 1 | 1 |
| 2 | 16 |
| 3 | 174 |
| 4 | 2144 |
| 5 | 29900 |
| Total | 32235 |

None of the 32,235 determinants is a square. The output retains every distinct determinant, its frequency and an example signed graph. This excludes a local family omitting both spokes. A separate independent checker, `scripts/check_spoke_gram_modular.cpp`, uses degree-completion DFS and modular Gaussian determinants. It independently reproduced all 32,235 graphs and rejected every determinant as a quadratic nonresidue modulo one of 5,7,11,13,17. Its five arithmetic controls passed. Results are retained in `experiments/2026-10-03/spoke-modular-audit/result.json`; no exact determinants from this generator were reused by that checker.

## Essentiality implication

For a shared five-block T union{d,u} at a star spoke, the three triples containing d and two points of T occur in both star blocks. The other three d-triples are {a,d,u}, one for each a in T. Such a triple is private exactly when a's local quadruple family omits {d,u}. Thus point-essentiality requires each spoke to be missing in at least one of the three local families. The independently checked both-spokes obstruction therefore forces at least two different local families to omit complementary spokes. Three projective-plane families fail this condition.

This is a local restriction within the full regular multiplicity-seven branch. It neither produces a 16-point cover nor excludes all 64-block covers.

```sh
python3 experiments/2026-10-03/thirteen-point-links/check_both_spokes_determinants.py
```
