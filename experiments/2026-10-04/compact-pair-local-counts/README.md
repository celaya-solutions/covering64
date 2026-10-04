```
Document:    Prepared Compact Full-Universe Pair-Local Count Model
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      db1f64fad63069aaa72ea2ffe21f0fa4781adec41811dd6f5c086807516ff192
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Prepared compact full-universe local-count model

The model is frozen and prepared only. No optimizer has run, no runner has been
prepared, and an independent gate is required before any run. It has 7,428
variables, 16,224 rows, and all 4,368 possible five-block variables in zero-based
lexicographic order. Point labels remain one-based.

## Model layout

| Variables | Count | Inclusive IDs | Domain |
| --- | --- | --- | --- |
| Block indicators | 4,368 | 0–4367 | 0 or 1 |
| Exact pair counts | 120 | 4368–4487 | 5 through 64 |
| Exact triple counts | 560 | 4488–5047 | 0 through 64 |
| Exact quadruple counts | 1,820 | 5048–6867 | 0 through 12 |
| Exact hole flags | 560 | 6868–7427 | 0 or 1 |

| Rows | Count | Inclusive row IDs |
| --- | --- | --- |
| Exactly 64 blocks | 1 | 0 |
| Count definitions | 2,500 | 1–2500 |
| Hole channels | 1,120 | 2501–3620 |
| Pair/triple cuts | 1,680 | 3621–5300 |
| Pair/quadruple cuts | 10,920 | 5301–16220 |
| Audited core caps | 3 | 16221–16223 |

Every count equals the sum of all block indicators containing that set. Pair,
triple, and quadruple supports have 364, 78, and 12 block variables respectively.
For each triple, its hole flag is true if and only if its exact count is zero.
The objective is `65*holes + original_core_overlap`. All three checked core
overlaps are at most 55.

The model includes every row `3*c(P)-c(T)>=13` for P contained in T and every
row `3*c(P)-2*c(Q)>=12` for P contained in Q. It omits the earlier global DP and
named partition filters. It imposes no equal-degree, incidence, family, or
symmetry restriction. Any future output still needs the global profile scan and
both covering verifiers; omission from the model is not permission to skip them.

## Why every valid 64-block cover remains represented

Start with any 64 distinct five-blocks covering every triple on labels 1 through
16. Set precisely their block indicators to one. All 4,368 block options exist,
so this assignment is available regardless of incidence pattern or labeling.
Define each auxiliary count by its containing selected blocks. The upper bounds
are valid because at most 64 blocks are selected, and only 12 distinct blocks
can contain a fixed quadruple.

Fix a pair P. Its fourteen containing triples must be covered, while each block
through P covers three of them. Hence c(P)>=ceiling(14/3)=5. Every triple count
is positive, so setting all hole flags to zero satisfies both directions of every
hole channel.

For T=P union {a}, the exact identity
`3*c(P)-c(T) = sum(c(P union {x}) for x outside T)` has thirteen terms. Each is
at least one in a full cover, proving the triple cut.

For Q=P union {a,b}, the identity
`3*c(P)-2*c(Q) = sum(c(P union {x}) for x outside Q)`
`+ [c(P union {a})-c(Q)] + [c(P union {b})-c(Q)]`
has twelve covered triple terms and two nonnegative differences by containment.
This proves the quadruple cut without any degree or block-count assumption.
The independent proof receipt checks all nonzero column identities and sharp
full-cover controls, and rejects damaged coefficients/constants.

The three core caps follow the separately checked rational certificate and
relabeling audits: any 56 blocks of each 60-block core require more than the
eight remaining blocks available in a 64-block cover. Thus every valid cover
has overlap at most 55. These proof files and their source/input bindings are
listed in the manifest and preserved with the preparation.

Therefore each valid 64-block cover has its unique count extension and zero
holes in this model. The optimization model also admits near-covers, so a
bounded run cannot prove a global lower bound. A CP-SAT infeasibility response
would still require an independently checked unrestricted proof certificate.

## Guidance is explicitly infeasible

The saved guidance is the earlier six-hole state, SHA256
`797dada195b23eecc808798eb12c8e4e7ccd7edd026fbdf22dea5b341f9ea2de`.
Only the 4,368 block indicators are hinted, with 64 ones; all 3,060 auxiliaries
are unhinted. This does not fix any variable. The solver may repair or reject the
hint.

Its uniquely derived complete assignment violates exactly four triple-cut rows
and is not feasible. `guidance-diagnostic.json` records these rows and binds a
separate derived-value vector for audit. The displayed value 392 is the
hypothetical seed objective, not a feasible incumbent or solver result.

## Frozen evidence and planned budget

Preparation source: `91dc8b7a3d86113e516fa006744567ed331efb64bd41c5444be04d03dac4dce0`.
Manifest: `21a539f225d1743fbdfe7547f8fd5357b6f500a7ac6edbfb3e258ed5e7257ff2`.
Model: `78c229e5962f180fe60ffcc4b6d495681671082bd7cc1280bc621b9fec899f40`.
Parameters: `a72db619575952d0899a8b1c65a9196f5c025c05e2b153ab019988ebff7c5e3f`.

The 6,031,619-byte model, parameters, exact guidance file, diagnostic vector, and
all source/input snapshots are preserved under ignored
`experiments/scratch/compact-pair-local-counts-20261004/`.
`universe.json` stores the full canonical universe; `files.json` binds the small
local artifacts. `build-stats.json` contains preparation-only measurements.

The saved parameters plan one 120-second run with four workers and seed
2026104301, with search logging enabled and direct solver stdout disabled.
No model run is authorized by this preparation record. Keep this frozen sibling
unchanged if a later, stronger model is prepared separately.
