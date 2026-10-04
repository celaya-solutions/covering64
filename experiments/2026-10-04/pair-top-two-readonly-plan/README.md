```
Document:    Read-Only Top-Two Extended Formulation Plan
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      7ffd867f16944520b33be77bf520adad95f5520a730d57507e9bcff778f534ae
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Read-only plan: top-two extended formulation

Status: proposal only. No model, hint, runner, or optimizer was constructed or
executed for this plan. The prior 120-second compact two-triple run returned
UNKNOWN without a feasible assignment; that result does not prove infeasibility.

## Exact replacement

For each of the 120 pairs P, write r=c(P), and t_a=c(P+a) for its 14 distinct
outside-point positions. The existing 91 inequalities are

    t_a + t_b <= 3*r - 12  for every distinct outside pair a < b.

Introduce one integer z_P in [0,64] and fourteen integer y_Pa in [0,64], with

    y_Pa >= t_a - z_P
    2*z_P + sum_a y_Pa <= 3*r - 12.

Nonnegativity is a variable-domain bound, not an extra constraint row. Do not
replace the fourteen distinct positions by distinct numerical count values.

Forward proof: for any distinct a,b, t_a+t_b <= 2*z+y_a+y_b <= 2*z+sum y,
so every original inequality holds. Conversely, let z be the second-largest
of the fourteen counts, counting ties at distinct positions, and let
 y_a=max(0,t_a-z). Then 2*z+sum y is exactly the sum of the largest two counts.
These assignments are integral and within [0,64] for integer t in [0,64].
Thus the existential integer projection onto all original variables is equal
to the original model. Every covering-preservation argument for the original
stronger cuts is retained, subject to independent verification of the new
implementation and unchanged original constraints.

The same proof with continuous z,y establishes equality of the projected LP
relaxations for this replaced family. There is no stronger LP bound merely
from this rewriting. CP-SAT presolve, propagation, and search can behave
differently; no performance benefit has been measured.

## Proposed size, retaining all other rows

| Item | Frozen explicit model | Proposed extended model |
|---|---:|---:|
| Block Boolean variables | 4,368 | 4,368 |
| Pair and triple integer counts | 680 | 680 |
| Exact hole Boolean variables | 560 | 560 |
| New threshold integers | 0 | 120 |
| New hinge integers | 0 | 1,680 |
| Total variables | 5,608 | 7,408 |
| Total constraint rows | 14,404 | 5,284 |

The 10,920 explicit two-triple rows become 1,680 hinge rows plus 120 budget
rows. All 1,680 single-triple cuts and all three core caps remain. The new
constraint count is 1 cardinality row + 680 count equations + 1,120 exact
hole reifications + 1,680 single-triple cuts + 1,680 hinge rows + 120 budgets
+ 3 core caps = 5,284. The replaced family has 7,080 direct linear coefficient
entries rather than 32,760, excluding variable-domain bounds and unchanged
constraints. There are 1,800 more variables and 9,120 fewer rows.

Keep all 4,368 block variables in zero-based lexicographic order, exactly 64
selected, pair-count domain [5,64], triple-count domain [0,64], and objective
65*holes + original-core overlap. Do not introduce degree-20 constraints,
symmetry restrictions, family restrictions, or incumbent-incidence assumptions.
Do not add a fourth core cap to this plan without a separate scope decision.

## Optional, separately gated removal of single-triple cuts

The exact count definitions imply sum_a t_a=3*r, including for fractional
block variables: every block containing P contributes to three outside
positions. Fixing a and summing its thirteen explicit two-triple rows gives

    13*t_a + (3*r-t_a) <= 13*(3*r-12)
    t_a <= 3*r-13.

This is exactly the single-triple cut, over real as well as integer variables.
Consequently those 1,680 rows are redundant given the full stronger family and
exact incidence equations. Removing them would give 3,604 total rows, with
the same projected LP relaxation. This removal is not part of the conservative
5,284-row proposal and needs its own audited implementation gate. An independent
agent checked this algebra and the extended-formulation algebra read-only.

## Completing a feasible hint

Given any fixed family with D2max=0, the formula above provides its canonical
z/y extension. A complete model hint additionally requires 64 distinct valid
blocks and satisfaction of every unchanged model constraint, including all
three core caps. D2max=0 alone is not a certificate for the core caps.

1. Independently parse the 1-based blocks, reject malformed or duplicate blocks,
   and map them into the full lexicographic block universe.
2. Assign every block Boolean, including all zero positions. Recount all 120
   pair and 560 triple counts directly from the selected blocks.
3. Assign each of the 560 hole flags to 1 exactly when its triple count is zero.
4. For each pair, sort its fourteen counts with outside point as a deterministic
   tie-break, assign z to the second-largest count, then all fourteen y values
   to max(0,t-z). Sorting chooses positions, not distinct numeric values.
5. Evaluate all model rows, domains, reification conditions, and the objective
   from this full vector independently. Check all three core overlaps <=55.
6. Add each of the 7,408 variable indices exactly once. Audit unique indices,
   full coverage, and values against the frozen model's actual variable names
   and order. Record hashes of the candidate, model, complete vector, and hint.

For integer block families, D2max=0 also implies pair-count >=5: the top-two
sum is at least (3*r)/7, so 3*r/7 <=3*r-12 gives r>=14/3, hence r>=5. The
single-triple constraints follow from the identity above. These deductions
do not excuse checking the actual full hinted vector at the gate. A family
with holes can be feasible for this hole-minimizing model without being a
covering witness. Keep those claims distinct.

The existing H6 has D2max=14/D2sum=62; H48 has 75/175; H49 has 74/170.
None admits a feasible z/y extension. H48 and H49 having zero D3/D4 does not
change that conclusion. They must not be described as feasible hints for the
strong model. A future native hint construction is separate work.

## Independent gate needed before preparation or execution

Root must decide whether to prepare the conservative or reduced model. After
that authorization, a separate gate must check the symbolic projection proof,
domains, all 120 pairs and 14 distinct positions per pair, count-support
completeness, exact hole semantics, all retained caps, objective, variable order,
and absence of additional restrictions. The checker must read the frozen
serialized model independently, not trust builder-reported totals.

Finite controls should cover ties, all-equal counts, zero counts, one or several
positive positions, both domain extremes, and exact boundary/pass/fail budgets.
Check canonical extensions against all 91 original inequalities per pair and
all 1,800 new rows. Seeded synthetic controls support the algebraic proof;
they do not replace it. A complete hint requires its own full-vector gate.

Freeze source revisions, solver version, model/manifest/hint/parameter hashes,
and the independent GO receipt before any authorized optimizer call. Retain
both prior covering-verifier paths for any returned candidate, including
malformed, duplicate, and damaged controls. Preserve raw logs and witnesses;
UNKNOWN remains inconclusive. No new execution is authorized by this note.

## Sources bound by this plan

- Frozen explicit model: `../compact-pair-two-counts/manifest.json`, SHA256
  `82372b924493eed1e3a24c48e580d0b15796cc1d2c50bbe71b400bee23910aad`.
- Frozen builder: `../compact-pair-two-counts/prepare.py`, SHA256
  `dd615064bcf96fd28a62fe13859874c417ff050ff60198bf62a1f4efdb8115ae`.
- Stronger-cut independent proof: `../pair-two-necessary-cuts-independent/audit.json`,
  SHA256 `db490b9d3cd3500eb2c85d36f803a73667ceed00e5251932608e7d1150e7099b`.
- Independent finite recount: `../native-d2-readonly-inventory/result.json`, SHA256
  `f67e7233abb90a739b194cbba1f461cba12a99a6aa18b1c909c8ea697d8be6ed`.
