```text
Document:    Independent Affine Link Support Certificate Replay
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      4d711d902babae39a6ab8805c5f10776a3165cb6d1ad8ffefb2375aaec171c28
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent support-certificate replay

The independent bitset replay agrees with every field of all 256 saved cases and every
propagation round. It excludes 249 fixed affine partials: 173 by insufficient triple
support and 76 by incompatible forced blocks. Seven fixed partials survive this screen.
All sixteen selected point-one partials are excluded. Survival is not feasibility.

The checker enumerates the full 4,368-block lexicographic universe and starts each case
with all 3,003 blocks avoiding its fixed point. It reconstructs all 455 exact residual
triple demands from the pinned recipe and twenty-block partial. A block meeting a
zero-demand triple cannot be selected, so removing it is exact. A row with fewer
remaining blocks than its positive demand is impossible. A row with support equal to
its demand forces every supporting block. If forced blocks exceed any row demand,
the branch is impossible; otherwise their contribution is subtracted and propagation
continues. Every saved support list is compared with the complete independently rebuilt
support, not just checked for membership.

The implementation uses integer bitsets and precomputed triple-to-block incidence.
It imports neither producer module and calls no optimizer. It checks candidate-pool
hashes, all forcing reasons, residual totals, fixed blocks, terminal certificates,
summary counts, and the seven survivors. Every point-avoiding domain is complete;
no incumbent core, degree, or rotational restriction is added. Eighteen damaged
certificate controls are rejected. Ruff passes.

The seven survivors, written as (profile seed, point), are (0,10), (40,13), (4,7),
(18,3), (16,3), (16,8), and (60,3). Their local shapes are C4 with a leaf except
(40,13) and (60,3), which have a triangle with a two-edge path. Initial retained
candidate counts range from 180 to 493. At most three propagation rounds occur.

Each exclusion applies only to the exact saved twenty-block partial under its fixed
excess profile. This does not exclude other affine embeddings, other local decompositions,
the profile itself, or a general 64-block cover. A future completion search from one
survivor remains a conditional branch. The existing independent construction receipt
is bound by hash; its dual-verifier checks cover all 256 partials.

The checker refuses to overwrite its saved receipt. Use a fresh sibling directory for
another replay. Source, producer, construction, and input hashes are recorded in the
review and file index.
