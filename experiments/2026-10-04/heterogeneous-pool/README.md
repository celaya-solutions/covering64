```text
Document:    Heterogeneous Elite Block Pool Construction Pilot
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      4cd0fa644116f1f2d21d0d73448721f3d74a3b2c97c74f0f15b80a65d1d5125c
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Heterogeneous elite-block recombination

This construction pilot combines ten independently checked 64-block partial
covers from the unrestricted, regular, SQS, native, graph-1 and graph-5 work.
The first pool is their union of 277 distinct blocks. The second adds 60 blocks
sampled without replacement from its complement using seed 2026104091.
The source inventory records hashes, both cover-checker receipts, separating
degree/pair/triple histograms, and pairwise overlaps. The two three-hole seeds
retain a known forbidden core; this pilot does not assume their blocks must stay.

Both models retain all 4,368 global block variables in lexicographic order,
with 1-based point labels. Exactly 64 variables are selected. A single zero-sum
row forbids blocks outside the specified pool. For each of the 560 triples,
one Boolean is equivalent to zero coverage, using two enforced linear rows.
The objective is the exact number of missing triples. No degree, hub, heavy-link,
symmetry or graph-specific constraint is added. The complete three-hole hint
is feasible in both models. Every triple has at least two eligible carriers.

Each case has a 30-second budget and four CP-SAT workers. The two frozen
models, parameters, solver logs and responses are kept in ignored scratch.
`manifest.json` binds the source, seed files, model bytes, pool membership,
random additions, Python version, OR-Tools version and budgets. An independent
gate must bind that manifest before either solve. Every saved state must then
pass the package verifier and separate standalone checker; an incomplete state
is only a partial cover. Timeouts and solver bounds do not prove a global result.

The small-pool recombination idea follows the already reviewed Dai thesis
and Dai, Li and Toulouse, *A Cooperative Multilevel Tabu Search Algorithm for
Covering Design Problem*, [doi:10.1007/11740698_11](https://doi.org/10.1007/11740698_11).
The publisher abstract was rechecked on October 4. This experiment is an
adaptation, not a claim of a new algorithm or a reproduction of that paper.

## Status

Both authorized cases finished with status FEASIBLE. The 277-block case ran
30.010944 seconds; the 337-block case ran 30.002212 seconds. Both callback streams saved
the same original three-hole hint, with no lower objective. Final solver
responses can contain different equal-objective states; the independent
postcheck extracts and checks those separately. Package and
standalone verifiers independently agree that each saved state has 64 distinct
blocks, covers 557 of 560 triples, and is incomplete. The recorded canonical
hash is `d6dcfd2f1778f76c90ca67698865f683a44a6b69ddacad8f77cc4ee9021eacdf`.
These bounded runs do not establish that either pool cannot improve.

The independent final-response checks passed. The two final assignments each
have degree histogram 19:2, 20:12, 21:2, with three missing triples and the
original 60-block core still present. Their canonical hashes differ from the
first callback hint. New equal-score assignments therefore did not escape
that core or lower the missing-triple count. See
`../heterogeneous-pool-independent/postcheck.json` for the checked outcomes.
