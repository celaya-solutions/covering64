```text
Document:    Independent Audit of the Six Hub Count Cases
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      ced28d8a31e921dc2cdbf68476d44bba17ed8ca7a5e0894c4dfa8808919b4638
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Scope and result

The six pairs `(m4,z)` with `m4` in `{0,1}` and `z` in `{0,1,2}` form a
disjoint necessary partition of integer normalized regular 64-block covers
with four sevenfold triples. They do not partition unrestricted covers without
first establishing this branch. No single case is equivalent to the branch;
excluding it requires checked exclusions in all six cases.

`check.py` independently enumerates the four all-hub triples and the
multiplicity-five hub pairs. Each such pair has one excess incidence beyond
coverage. This bounds each hub-triple multiplicity by two. Enumerating all 16
possible doubling subsets gives `z <= 2` in both hub graph cases. Counting
all-hub triples then gives `m3 + 4*m4 = 4+z`, hence `m4 <= 1`.

The checker reconstructs both equations directly from all 4,368 global
lexicographic blocks. All twelve exported models (cycle/matching times six
cases) add exactly two rows and no variables, preserving every previous
proto field. The first row counts the 12 blocks containing all four hubs;
the second counts hub-triple incidences in 276 blocks, with coefficients 1 or 4.
All 120 damaged-model controls are rejected. Forty-six invalid scopes are
rejected without mutation, including wrong counts and types, wrong branches,
changed variables, missing required rows and duplicate application. When a
required row has exact duplicate encodings, the control removes every copy.

# Evidence and replay

`audit.json` contains the full model list, source hashes, independent necessary
count patterns, damaged-model checks and input-rejection evidence. The
helper SHA256 is
`6a3bc55e12b50ddb06e1905c07335b88d9437c71cd19aec1bd9bf8e89e7c7ee6`.
The frozen sources, full-cut bases and twelve outputs are in
`../../scratch/four-seven-hub-split-independent`.
The bases match the independently audited v1.1.0 prepared CP archive.

Run `uv run python experiments/2026-10-03/four-seven-hub-split-independent/check.py`.
The checker refuses to overwrite an existing completed audit. Preserve the
prior result before rerunning. It performs no optimization and reports no
integer cover or exclusion.
