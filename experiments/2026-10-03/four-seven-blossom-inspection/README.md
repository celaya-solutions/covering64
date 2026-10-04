```text
Document:    Heavy-Link Blossom Cuts and Saved-Primal Inspection
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      6302a0c2126413e33069adea1c2380085e88114f1175ee19051febd9426c6b6e
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Result and scope

The saved fractional solutions for 42 of the 158 remaining cases violate
54 odd-set inequalities. There are 42 distinct case/group/subset inequalities
among these violations. The maximum excess is `0.23825660639485546`, while
the maximum measured heavy-link degree residual is `9.277023593767808e-13`.
The threshold for reporting violations was `1e-7`.

Cycle contributes 27 affected cases and 33 violations; matching contributes
15 affected cases and 21 violations. No fixed first-heavy link violates a
cut. All reported violations concern the other three heavy links. These are
numerical measurements of the saved fractional solutions, not new exclusions
of integer cases and not evidence that a 64-block cover exists.

The strongest affected saved solutions are `matching-029`, `matching-113`,
`matching-038`, and `cycle-046`, in that order. The three-other-hubs subset
`{4,12,16}` for the heavy triple `{5,6,7}` is violated in five matching
solutions and four cycle solutions. A different feasible fractional solution
can change these rankings.

# Elementary validity proof

Fix one heavy anchor triple `{a,b,c}` and its own hub `h`. Its seven selected
blocks induce a simple graph on the 13 outside points: a block containing the
triple corresponds to its two outside points. Full triple coverage forces
every outside vertex to have graph degree at least one.

For an outside point `p != h`, the normalized branch has pair multiplicity
`lambda(a,p)=5`. Thus there are 15 incidences covering the 14 triples through
that pair. Blocks containing exactly two anchors are forbidden. Consequently
the triples `{a,b,p}` and `{a,c,p}` both have multiplicity equal to the heavy
graph degree `d(p)`. Coverage of the other 12 triples gives
`2*d(p)+12 <= 15`. Since `d(p)` is an integer at least one, it is exactly one.
The seven graph edges have total degree 14. The twelve outside points other
than `h` use degree 12, so the remaining hub has degree two.

Write these degrees as `b(h)=2` and `b(p)=1` otherwise. For every subset `S`,
the integer edge counts satisfy

```text
b(S) = 2*x(E(S)) + x(delta(S)).
```

When `b(S)` is odd, its nonnegative integer cut size `x(delta(S))` is odd and
therefore at least one. This proves
`x(E(S)) <= floor(b(S)/2)`. The result is a valid integer consequence of the
full normalized regular branch. It is deliberately stronger than the basic
fractional model. The helper does not require the auxiliary double lift.

The total degree is 14 and there are seven edges, so the inequality for the
complement of `S` is equivalent under the degree equations. There are 13
outside vertices, hence exactly one of a complementary pair has size at most
six. This gives 2,048 canonical odd subsets per heavy triple. Twelve singleton
non-hub subsets give `0 <= 0`; twelve hub-plus-one subsets give a unit variable
bound. Omitting only those 24 tautologies leaves 2,024 rows per heavy triple,
or 8,096 rows in total. Rows retain variables already forced to zero by the
base model, so even a structurally empty internal edge set stays a proper
linear row. No variables are added.

Each target heavy graph has the same directly proved degree pattern. Exact
point relabelings biject its subset and edge templates with the first graph.
These template maps need not preserve every other hub-pair constraint. No
symmetry of an unknown cover and no completeness theorem for the fractional
polytope is assumed.

# Checks and evidence

The seven focused tests passed in 26.58 seconds, and Ruff passed. They compare
every appended coefficient and bound with an independently enumerated bitmask
template, verify all four transports, preserve every pre-existing model field
(including an objective and hint), and reject duplicate application, wrong
cases, reordered variables, relaxed coverage, and damaged degree rows before
mutation.

`validate_templates.py` independently enumerates all 29,970 allowed labeled
integer link graphs. Every graph passes all 2,024 retained first-link rows:
60,659,280 direct integer inequality checks. Exact coefficient and subset
transport validates all four heavy graphs, covering 242,637,120 inequalities.
All maximum integer excesses are zero. Of the 2,024 templates, 2,021 attain
equality; the three remaining rows are the retained all-forbidden triangles.
This finite test supports the implementation; validity follows from the
elementary proof above.

The scan reads the existing primal archive under
`experiments/scratch/four-seven-lp-primal-inspection-20261003`, checks each
primal hash and representative identity against saved records, and does not
invoke a solver or modify that archive. The full numerical violation archive
is stored under ignored scratch in `four-seven-blossom-inspection-v1.0.0`.
Each reported violation is recomputed by direct scalar summation and checked
against its complement. `summary.json` records hashes, tolerance, versions,
all 158 case rankings, and the most frequent violated cuts.

The helper and tests are frozen with before/after raw protobufs under ignored
scratch in `four-seven-blossom-cuts-v1.0.0`. Both lifted base models have 4,768
variables and 4,270 rows. Both blossom models retain 4,768 variables and have
12,366 rows. The exact-search reviewer owns the independent raw-model audit.

An initial scan command used the temporary script name `inspect.py`, which
shadowed Python's standard-library module during NumPy import. It failed
before producing an archive. The script was renamed `run.py`; the recorded
scan then completed. An initial template-validation run passed with a style
warning; after wrapping the line, the final source was rehashed and rerun.
No helper behavior changed after the focused tests.
