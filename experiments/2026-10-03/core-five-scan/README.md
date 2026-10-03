```text
Document:    Restricted Five-Removal Scan and Exact Triangle Obstruction
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      1f3ef0aa28ad9e39c97a7aaed50316f7b0811a3b9931e2ec82f7ac1dda4a7d98
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Restricted five-removal scan and exact local contradiction

All 909 symmetry classes in this restricted scan are excluded. This does not
exclude every five-removal set and does not establish a global lower bound.

The scan extended the 20 four-removal representatives with the smallest exact
dual bounds, ordered by bound and then lexicographic removal indices. Each was
extended by each possible fifth removed core block. Deduplication used only the
verified 60-element core-preserving subgroup. The standard-library scan checker
reconstructs this entire restricted family and checks each rational dual against
all 4,368 possible additional blocks.

Of the 909 classes, 908 had an exact dual greater than nine. One had a rounded
dual of 2,249,997/250,000 = 8.999988. Its removed core indices are
**[1,22,23,25,29]**, using 1-based positions in the canonical 60-core list. It
retains 55 blocks and would need nine additions for a 64-block cover.

## Compact contradiction for the remaining class

Its rounded dual reconstructs to an exactly feasible dual of nine, with
numerators over denominator five: sixteen weights of one, thirteen of two,
and one of three. All 30 weighted triples are uncovered by the retained core.
There are 55 uncovered triples in total. Exactly 50 possible added blocks have
dual load one. Any nine-block completion must therefore use only those tight
blocks and cover each positive-weight triple exactly once.

Let

- A = {1,2,3,4,6}
- B = {1,2,3,6,7}
- C = {1,3,4,6,7}.

Among all 50 tight blocks, triple {1,2,6} is covered only by A or B;
{1,4,6} only by A or C; and {1,6,7} only by B or C. These three requirements
force at least two of A, B, C to be selected.

But A and B share positive-weight triple {1,2,6}; A and C share {1,3,4};
and B and C share {1,3,7}. Since each weighted triple must be covered exactly
once, at most one of A, B, C can be selected. This contradiction excludes the
specified retained-core neighborhood without trusting a solver result.

`five-removal-triangle.json` contains the exact core, removals, rational dual,
and these six triple witnesses. Its standalone checker reconstructs all
possible blocks and verifies both the capacity bound and the precise carrier
pairs. Eleven positive and damaged-certificate controls passed. The parent
agent also recorded an independent exhaustive tight-kernel check in
`independent-kernel-tree.json`; the triangle proof does not depend on it.

## Evidence and reproduction

```sh
uv run python scripts/scan_core_five_removals.py --parents 20
python3 -I scripts/check_core_five_scan.py experiments/2026-10-03/core-five-scan/five-removal-scan.json.gz
python3 -I scripts/check_core_triangle_obstruction.py experiments/2026-10-03/core-five-scan/five-removal-triangle.json
uv run pytest -v tests/test_core_triangle_obstruction.py
```

`verification.json` records both standard-library checker outputs, source and
artifact hashes, and the exact scope. `five-removal-scan.json.gz` contains all
909 raw rational duals and selection metadata. `lp-uncertified-candidates.json.gz`
retains the original screening output; its sole candidate was subsequently
excluded by the triangle certificate. `candidate-tight-dual.json` records the
exact denominator-five dual and all 50 tight blocks. Raw source snapshots,
case logs, generation output, and test output remain outside Git under
`experiments/scratch/core-five-scan-20261003/`.

The generation used GLOP with no time limit or random seed, visiting the finite
specified set in a fixed order. Its source hashes, base revision, versions,
start time, and 12.352-second LP/checking-loop duration are saved in the scan.
The rational certificates, not solver status or floating-point optimality,
justify each exclusion.
