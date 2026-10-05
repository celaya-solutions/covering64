~~~text
Document:    Stratified Prime-101 Residual Equation Benchmark
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      31484d1fd2b408a9b098d648e0158154d012f1c5c636e7a255b27495eb29184e
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
~~~

# Completed finite benchmark

All 32 selected cases completed in 1.607 seconds under the authorized
15-second cooperative budget. Gaussian elimination modulo the prime 101 found
four contradictions and 28 consistent field systems. Every contradiction has
a directly checked row-combination certificate; every consistent case has a
directly checked field solution. No optimizer or full 616-case screen ran.

| Source | Core | Cases | Contradictions | Field-consistent |
|---|---|---:|---:|---:|
| Expanded sample | C5 | 1 | 0 | 1 |
| Expanded sample | C4 with a leaf | 1 | 0 | 1 |
| Expanded sample | Triangle with a length-two path | 2 | 1 | 1 |
| Original | C4 with a leaf | 11 | 1 | 10 |
| Original | Triangle with a length-two path | 11 | 2 | 9 |
| Original | Triangle with leaves at distinct vertices | 6 | 0 | 6 |
| Total | | 32 | 4 | 28 |

The four excluded cases are:

| Catalog | Full pair ordinal | Core | Eligible variables | Rank of A mod101 |
|---|---:|---|---:|---:|
| Expanded sample | 1,266,773 | Triangle with a length-two path | 458 | 390 |
| Original | 54,692 | C4 with a leaf | 374 | 374 |
| Original | 4,949 | Triangle with a length-two path | 373 | 373 |
| Original | 99,638 | Triangle with a length-two path | 430 | 390 |

The first row excludes one of the four expanded cases that passed the parity
check. The other three expanded cases remain consistent modulo 101. A field
solution does not supply binary blocks and is not a cover witness.

# Frozen pool and deterministic selection

The source is `../affine-mod2-pilot/result.json`, SHA256
`aacc0a5cd51bc8315e8b72dd1f14d7376b4241237672fbbceceec6d7e3288c71`.
The manifest also pins that run's archived `executed-source.txt` to the actual
source hash in its receipt, rather than relying on a potentially changed
working source file.

The parity-consistent pool has 616 cases: 612 original cases and four expanded
sample cases. The original cases split into 226 C4-leaf, 380 triangle-path2,
and six triangle-two-leaves cases; there are no original C5 cases in this pool.

The plan includes all four expanded cases and all six rare original cases.
It also takes eleven evenly spaced positions, including both endpoints, from
each of the two larger original core classes. Cases within a core are sorted
by zero-demand eligible-domain size, then GF2 nullity, then full pair ordinal.
For n cases and k samples, selected position j is `floor(j*(n-1)/(k-1))`.
`plan.json` saves all exact source-result indices and catalog/profile/partial
IDs. Expanded cases run first; the selected original core strata are then
interleaved. This is a fixed stratified benchmark, not a random sample.

# Original equations and exact contradiction certificates

All point-one partials and profiles are rebuilt from their frozen original
catalogs. Before any removal, the candidate variables are all 3,003
five-subsets of labels 2 through 16, in global lexicographic block order.
The 455 triple rows use lexicographic triples on labels 2 through 16.
Row 455 is the cardinality equation requiring 44 selected blocks.

For each triple t, the residual demand is `1 + e_t - l_t`, where e_t records
the profile excess and l_t records coverage by the fixed point-one partial.
The demands sum to 440. Only candidates meeting a zero-demand triple are
removed. This removal is valid for the original binary system because its
coefficients and variables are nonnegative. There are no propagated forcing
cuts, incumbent cuts, heuristic cuts, or parity-derived domain cuts.

The retained matrix A includes all 455 triple equations and the sum44
equation. Its right-hand side is b. The program forms `[A | b | I_456]` and
performs row swaps, nonzero pivot normalization, and forward elimination
modulo 101. NumPy int64 operations track each row as an explicit combination
of the 456 original equations. Every update is reduced modulo 101 before the
next update; products of reduced entries are at most 10,000, far below the
integer range limit. Direct certificate dot products are also safely bounded
by these small dimensions and entries.

For an inconsistent system, the saved dense vector y has 456 coefficients
in 0 through 100. Before accepting the case, the producer checks
`y A = 0 (mod101)` for every eligible variable and `y b != 0 (mod101)`.
This is a finite contradiction certificate for that fixed partial/profile
system. For a consistent system, free field variables are set to zero and
back substitution constructs x; the producer directly checks
`A x = b (mod101)`. The saved rank and pivot columns come from the completed
echelon form. A timeout would carry only a partial rank and no completion claim;
none occurred in this benchmark.

These conclusions concern only the selected fixed-link/profile cases.
They do not classify all affine recipes, all local decompositions, or general
C(16,5,3) covers, and do not establish a global lower bound.

# Evidence and provenance

The source and all inputs were frozen before the benchmark. The runner has
only `prepare` and `benchmark` modes and rejects replacing its detailed result.
The cooperative timer includes input validation, loading, matrix construction,
and elimination, with a 0.15-second finalization reserve. Python was 3.13.15 and
NumPy was 2.5.3. Ruff passes.

Source SHA256:
`040cefb73c53c93381a0928b98cdd5ad900799590e12dcec0184bd9e1871db72`.
Manifest SHA256:
`3ab0c3d2a37664fea42c099aa47ee3f5c3052fea15b4b120c3422b3e03f1d119`.
Plan SHA256:
`3dbc3eafd965fa8f2a6d7c92f98c50350d07a1a3521e5c598de7d84f82aff3ac`.
Detailed result SHA256:
`5b8997b6c50775fdb0d1e3a852b87b5d1b4ca4ee7d1ef690c8b3c586ba457154`.

`summary.json` is the compact tracked receipt. The detailed local `result.json`
is ignored and is also archived, without changing its contents, as
`experiments/scratch/affine-mod101-benchmark-v1.0.0/result.json.gz`.
The compact receipt records both the original and compressed hashes. The
detailed result saves each case's full domain IDs, removed zero rows,
rank/pivots, field certificate, outcome, and time. Root will independently audit
that evidence before any wider modular run.
