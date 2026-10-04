```
Document:    Independent D2 Recount of Three Fixed Families
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      3304e8f098c59adcc418af73a8591ab2f2886a7d8ca33e93fa7f0ae519ca6032
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent D2 recount of three fixed families

This diagnostic recounts raw subsets for three existing 64-block families.
It imports no producer metrics and makes no optimizer call. It changes no
candidate, model, hint, or search implementation.

For each pair P, the 14 outside points label 14 distinct triple positions.
Let top1 and top2 be the largest two counts at distinct positions; ties count
twice. Define

- D2max = sum_P max(0, 12 - 3*c(P) + top1 + top2).
- D2sum = sum_P sum_{a<b outside P} max(0, 12 - 3*c(P) + c(P+a) + c(P+b)).

The checker enumerates all 91 outside pairs for each of the 120 base pairs,
and checks that the maximum row deficit equals the top-two expression.

| State | Holes | D3 | D4 | D2max | D2sum | Violating pairs | Violating rows |
|---|---:|---:|---:|---:|---:|---:|---:|
| H6 | 6 | 4 | 0 | 14 | 62 | 14 | 62 |
| H48 | 48 | 0 | 0 | 75 | 175 | 75 | 175 |
| H49 | 49 | 0 | 0 | 74 | 170 | 74 | 170 |

D3 and D4 are the existing single-triple and quadruple deficit totals.
None of these states satisfies the stronger two-triple family. In particular,
zero D3/D4 for H48 and H49 does not make either a feasible strong-model hint.

## Provenance

The following source files were independently recounted:

- H6: `experiments/2026-10-03/reduced-family-heuristic/penalty-2026100363/search-control_before-1-h6.txt`; SHA256 `797dada195b23eecc808798eb12c8e4e7ccd7edd026fbdf22dea5b341f9ea2de`.
- H48: `experiments/2026-10-04/native-pair-penalty/seed-2026104401/search-final-qualified.txt`; SHA256 `630461e4c8805916ac515114b308d6ed05b2a43da16605ea452150d7e3a784d3`.
- H49: `experiments/2026-10-04/native-pair-penalty/seed-2026104402/search-final-qualified.txt`; SHA256 `a7feb783eb9f36e710feba5356857514cde146104b95de03fa47716126afd9c4`.

The existing independent postcheck is `experiments/2026-10-04/native-pair-penalty-independent/postcheck.json`
with SHA256 `7c58bbd14d7a07dafd92fa776e23adcc7d24cd1d2c622755da8c6b7454c8ca32`. It binds the prior dual
verifier checks; no fresh covering-verifier call was needed for this arithmetic
diagnostic. Checker SHA256: `aa292298f1f597ca2b4957466fc8f1799fee42dd94f877b4970337b4bd57e3a2`.

## Receipt and limits

`result.json` contains 120 per-pair records per family, including all 14
position counts, the two chosen distinct positions, maximum and sum deficits,
a histogram including zero deficits, and all violated rows. Its SHA256 is
`f67e7233abb90a739b194cbba1f461cba12a99a6aa18b1c909c8ea697d8be6ed`.

This is a finite arithmetic diagnostic, not a covering witness or a global
nonexistence proof. It does not measure a new search or establish that any
repair exists. The checker has an output-exists guard; retain this receipt
without overwriting it. Ruff passed for the checker.
