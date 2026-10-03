```text
Document:    Independent Modular Two-Spoke Obstruction
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      efc2bbfbd121cddaa44bfb2c7122a38d160eeafa39872fe77751038d0ade1667
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent modular obstruction for both missing spokes

Consider 13 distinct quadruples on 13 points, with every point in four quadruples. Suppose they cover every pair except possibly the seven edges of a fixed P3 plus five disjoint edges. No such family can leave both P3 spokes uncovered.

Let A be its square point-by-block incidence matrix. If H is the graph of missing pairs and F records excess pair coverage, then AA^T has diagonal four and off-diagonal entries 1+F-H. Every row sums to16, so F and H have the same degree sequence. If both spokes are missing, H is P3 plus m disjoint edges, for some m from0 through5. Only the hub has degree two; all other active vertices have degree one. Consequently F must be a simple graph, disjoint from H, with precisely those degrees.

The standalone C++ checker exhausts all F by pairing the largest remaining degree-one vertex. This differs from the first checker's enumeration of the two positive hub neighbors followed by a matching. Counts by m are0,1,16,174,2144,29900:32,235 total graphs.

For each candidate Gram matrix, modular Gaussian elimination finds its determinant to be a quadratic nonresidue modulo at least one of5,7,11,13,17. A Gram determinant det(AA^T)=det(A)^2 must be a square modulo every prime, including zero when divisible by that prime. All cases are therefore impossible. This replay uses no floating-point arithmetic and no Bareiss determinant code from the first checker.

Five arithmetic controls passed: the projective-plane Gram matrix, identity, an explicit nonsquare determinant, a directly built four-regular incidence Gram matrix, and determinant sign after a pivot swap. AddressSanitizer and UndefinedBehaviorSanitizer also passed and produced identical output.

The consequence for the point-essential regular64 branch with a multiplicity-seven triple is limited but useful: each of the two spokes must be omitted in some anchor's local family, and a single local family cannot omit both. At least two of the three families must therefore omit complementary spokes. This does not exclude the complete branch or establish a global covering bound.

Reproduce from the repository root:

```sh
clang++ -std=c++17 -O3 -Wall -Wextra -Werror scripts/check_spoke_gram_modular.cpp -o /tmp/check-spoke-gram
/tmp/check-spoke-gram
```
