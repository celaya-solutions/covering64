```
Document:    Finalized Top-Two Plan and Complete-Hint Helper
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      61b31b4cf770b8c5603384da65b46ca9cea33e5e40048c8c77d038b38a566155
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Finalized read-only top-two plan and derivation helper

The earlier plan is preserved in `../pair-top-two-readonly-plan/`. This version
uses four independently checked core caps and omits the redundant single-triple
cuts. It has 7,408 proposed variables and 3,605 proposed rows. No top-two model,
solver call, or accepted hint was produced.

For a pair P put r=c(P), t_a=c(P+a), with fourteen distinct outside positions.
Replace its 91 rows t_a+t_b<=3*r-12 by fourteen y_a>=t_a-z rows and one
2*z+sum(y)<=3*r-12 row, with integer z,y in [0,64]. Forward implication follows
from t_a+t_b<=2*z+y_a+y_b<=2*z+sum(y). Conversely z=the second-largest position
count and y_a=max(0,t_a-z) attain the largest-two sum exactly, including ties.
The same proof gives equal continuous projections after relaxing integrality.

Exact counts give sum_a t_a=3*r. Summing the thirteen stronger rows involving
one fixed a gives 13*t_a+(3*r-t_a)<=13*(3*r-12), hence t_a<=3*r-13. Thus all
1,680 single-triple cuts are implied over both reals and integers. The exact
agent independently checked both algebraic proofs. Keep pair domain [5,64].

The count is 4,368 block Booleans +120 pair counts +560 triple counts +560 hole
flags +120 thresholds +1,680 hinges =7,408 variables. Rows are 1 cardinality
+680 exact counts +1,120 exact hole reifications +1,680 hinges +120 budgets
+4 caps =3,605. Block order remains the complete lexicographic universe.

The reformulation and redundant-cut removal give the same projected LP region
as the explicit stronger model **with the fourth cap added to both models**.
The fourth cap can tighten the old three-cap model; this is not a stronger LP
claim for the extended formulation itself. No runtime benefit is established.
Keep the old objective 65*holes+original-core overlap for this hard model.

## Replayable helper

`derive_hint.py` is a pure derivation and validation utility. It builds no model
and imports no optimizer. For a candidate it independently recounts pair,
triple, and quadruple counts, exact holes, D2max/D2sum, old D3/D4, four audited
core overlaps, and the global forbidden-profile maximum. It calls both the
package and separate standalone covering verifiers and requires agreement.
The global profile uses weight5 for count>=6 plus1 for count>=7, maximizing
over disjoint triples; any partial family can be completed with zero-weight
positions to five disjoint triples on fifteen points. Its bound is26.

The helper evaluates every proposed row, both enforced directions of all exact
hole flags, and variable domains. Count equations use full-universe supports
independently from the selected-block recount. Four-cap IDs come from the
frozen three-cap manifest and independent fourth-core audit; their hashes are
checked before any derivation. It has malformed, duplicate, and damaged-input
checks and an output-exists guard.

Only a D2max=0 family passing every retained constraint can produce a semantic
complete vector. Hole-minimizing model feasibility does not require zero holes.
A covering witness additionally requires zero holes and both verifier passes.
The vector contains all block/count/hole/z/y values, including zero entries,
in a documented proposed order. It is **not yet a hint for a constructed model**:
a later independent gate must bind every actual model index/name/domain/row to
these values exactly once. No qualified vector has been emitted.

Run from the repository root, after a qualified candidate is available:

    uv run python experiments/2026-10-04/pair-top-two-readonly-plan-v2/derive_hint.py CANDIDATE --output NEW_RECEIPT.json

Omit --output for diagnostics only. Rejection exits2 and does not create a
receipt; an existing output is never overwritten.

## Controls and limits

`check_helper.py` checks811 finite count vectors, all65 threshold values per
vector, and2,433 boundary budget comparisons, plus exact replays of H6/H48/H49.
It confirms D2max14/75/74, D2sum62/175/170, and3,605 rows; H6 has fourth overlap59.
Malformed, duplicate, damaged, and valid nonzero-D2 families are rejected without
an output. The output-exists guard preserves its file. The receipt reports zero
models, zero optimizer calls, and zero hints written. These finite controls
support the algebraic proof, not replace it. Accepted full-vector output is
unexercised because no supplied family qualifies. Ruff passes for both sources.

The control receipt SHA256 is
`fa983136ad409dfd0b11a96647b13655f70d4eba6504e2c59c397e999a918cc7`.
Retain all prior frozen receipts. Any later model construction or execution
requires root authorization and a separate serialized-model/full-vector gate.
