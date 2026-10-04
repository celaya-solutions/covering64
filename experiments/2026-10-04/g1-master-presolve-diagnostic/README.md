```text
Document:    Fixed-g1 Identical-Model Presolve Diagnostic
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      247ddbff7e47c2f8ca0d74d9f622d457afd69420c1a921a459490ffe64b1e3aa
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```
# Identical-model presolve diagnostic

Two separately gated calls use the exact original 1,977-row, 276-variable
master, with model SHA256
`897b19ca1405688ba112feefa8ecd19190a886eed5f96964d52b87df30b7b06f`.
Both use a ten-second limit, one worker, seed 2026104070 and the same objective.
The only difference between these two calls is the explicit presolve Boolean.
No constraints, cuts, nogoods, objective terms or hints were changed between
cases. The prior inconclusive two-second run remains untouched.

| Setting | Master result | Master seconds | Replacement distance | Registry | Completion LP |
| --- | --- | ---: | ---: | --- | --- |
| Normal presolve | OPTIMAL | 6.360403082915582 | 6 | Rejected cycle-028 at anchor group 0 | Not called |
| Presolve off | OPTIMAL | 2.0344423750648275 | 6 | Accepted 061 / 107 / 086 / 087 | OPTIMAL, 13.514017967610794 |

The accepted tuple received one fixed-g1 completion LP with a one-second limit,
one worker and seed 2026104. It used 0.12420295807532966 seconds. The numerical
score did not improve the incumbent 7.52051548546158. There was no numerical
zero, exact fractional feasible point, stitched improvement or covering witness.

Total measured cost was **8.519048416055739 solver seconds** and
**9.960837500053458 wall seconds**. Both cases completed once. Launch revision
was `c80235d7fc403c6bdb9a7d06cf8134f6a267fae9`; OR-Tools was 9.15.6755.

The independent gate and postcheck in
`../g1-master-presolve-diagnostic-independent/` matched both complete model and
parameter/response protos, checked both four-link registry receipts, and
recounted the one LP primal residual as 13.514017967611121. They checked the
saved dual binding and budget totals. Full models, parameters, native logs,
responses, registry proofs and numerical vectors remain in the ignored raw
directory bound by `result.json`. No mathematical model mutation occurred.

The diagnostic shows that the original two-second cutoff was too short for
that normal-presolve startup. Presolve off was faster on this model and seed;
one comparison does not establish a general performance advantage. OPTIMAL
here is the solver status of the necessary-condition master, not a covering-
number theorem or an exact fractional completion certificate. The rejected
normal-presolve tuple was never sent to the completion LP.
