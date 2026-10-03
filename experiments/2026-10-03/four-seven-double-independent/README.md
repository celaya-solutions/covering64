```
Document:    Independent Double Triple Model and Rational Extension Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      e27608674bc87930e0d003916fd096c237b0d1f67344b01e39585d334b92865d
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent audit of the four-sevenfold double-variable models

Both saved models pass exact reconstruction of all 400 added Boolean variables
and all 677 added linear rows. Each has 4,768 variables and 4,270 constraints.
Removing the added suffix restores the entire previously audited full model
protobuf without changing any original field.

The added rows consist of 400 equations μ(T)=1+d(T), 156 fixed two-anchor triple
counts (144 singles and twelve doubles), one equation summing d to 44, and 120
pair-demand equations. The twelve internal-anchor pair rows are explicit linear
0=0 identities. All added variable names, Boolean bounds, ordering, coefficients,
and row domains are reconstructed from raw combinations and the proved counts.

The independent derivation of each pair demand uses the identity
Σ(T containing pair) μ(T)=3λ(pair), subtracting the heavy and fixed counts and
the baseline one for each of the 400 eligible triples. It does not use the
production helper as an oracle.

Both original rational LP witnesses extend to the 400 double variables. Every
new value is independently derived from weighted raw block containment and
compared to the saved extension. All 4,768 continuous variable bounds and all
4,270 linear rows are then evaluated with exact Fractions. Six controls per
case reject corrupted rows, missing equations, and an altered fractional double.
Neither extended vector is integral.

These checks prove the encoding matches valid integer full-cover consequences
and that its continuous relaxation is feasible at block weight 64. They do not
produce an integer cover or a nonexistence proof. In particular, an arbitrary
fractional witness of the original model need not satisfy the 156 strengthened
counts; these two specific vectors were checked and do satisfy them.

Run `uv run python experiments/2026-10-03/four-seven-double-independent/check.py`
from the worktree root. Large models stay in ignored scratch under
`four-seven-lp-20261003/strengthened`. The result records exact model and witness
hashes, row counts, negative controls, and the frozen independent base-audit hash.
