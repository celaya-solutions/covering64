```text
Document:    Bounded LP Farkas Screen for Affine Link Completions
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      59756ab4d6621012fbd0b956a49b1815b7cdc614095969bb05e5fbd2e8db2356
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Bounded LP screen of all remaining affine cases

## Question

Every case fixes one twenty-block point-one link from the affine catalogs and
one of the 1,300 circulant excess profiles. The other 44 blocks avoid point one
and must meet each residual triple exactly `d_t = 1 + e_t - l_t` times. This
screen asks whether even the bounded linear relaxation, `Ax = b` with
`0 <= x <= 1`, has a solution.

## Certificate

Columns meeting a zero-demand triple are dropped, as in the earlier parity and
prime-101 runs. For the remaining 0/1 matrix `A` (positive-demand triple rows
and the sum-44 row), an integer vector `Y` with

`b.Y - sum_j max(0, (A^T Y)_j) > 0`

proves infeasibility, because any `x` in `[0,1]^n` with `Ax = b` gives
`b.Y = sum_j x_j (A^T Y)_j <= sum_j max(0, (A^T Y)_j)`. GLOP only proposes `Y`
by maximizing that margin with `-1 <= Y <= 1`. The runner rationalizes the
proposal, scales it to integers and keeps it only if exact integer arithmetic
gives a positive margin. A case without an accepted certificate is reported as
open; none occurred.

## Run

Inputs are the 1,096 quiescent survivors of the original catalog's repeated
row propagation and the 207,474 survivors of the full new-only support screen.
All 208,570 cases received exact certificates in 564.97 seconds with eight
worker processes:

| Catalog | Cases | LP exclusions | Open |
|---|---:|---:|---:|
| Original chosen-witness catalog | 1,096 | 1,096 | 0 |
| Expanded new-only catalog | 207,474 | 207,474 | 0 |

Normalized LP margins were large: the 2,000-case trial had median 64.19 and
minimum 40.05. The relaxation is far from feasible, not borderline.

The certificate stream is ignored scratch data at
`experiments/scratch/affine-lp-farkas-v1.0.0/certificates.jsonl.gz`,
SHA256 `6bd6fb7868be952ab35fce6112ce5f302e7235ed31e21739976627e5ca2381eb`.
`manifest.json` and `result.json` are copied receipts. The runner SHA256 is
`e06fbfa99cd2a417067377bc7929507610f90a357be98f06241451b4c0fa34e8`.
Python 3.13.15 and OR-Tools 9.15.6755 were used.

## Scope

The four held conditional CP cases are among the 1,096 original survivors, so
they are now excluded and that batch is withdrawn rather than launched. The
result is conditional on the circulant `{+-1,+-3,8}` excess branch with exact
triple multiplicities from its profiles and a point-one link in the stated
affine recipe. It is not a global lower bound.
