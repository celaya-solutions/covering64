```text
Document:    Strengthened Eight Plus Eight Construction
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      cf5c91b50d884748ce4ffd9af3c904d04783cce6c9d4d6fe40abcd41f00ea1bb
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Strengthened eight-plus-eight recipes

These three models use exactly the same AA, AB and BB restricted construction recipes as the original experiment. All 4,368 variable domains, all 64 extension groups and the original 625 rows remain byte-for-byte equal in the model prefix. Additional rows are redundant consequences of full coverage inside this recipe. They do not reduce the unrestricted covering problem to this recipe.

For a same-half pair, let q be its incidence among the eight selected quadruples and x its incidence among extension pairs attached to the opposite half's triple bases. Its final multiplicity is 6-q+x, so the necessary pair floor gives x>=max(q-1,0). Type A has four q=0 pairs and 24 q=2 pairs; the 24 total extension-pair occurrences force x=0 and x=1 respectively. Type B retains the lower bounds.

For a point, let p count its opposite triple-base pair extensions and s its opposite quadruple-base singleton extensions. Covering all 28 pairs in the other half requires 9+3p+6s>=28, hence p+2s>=7. Type A has p=6. Therefore every singleton count is at least one; their total eight forces s=1 at every point and final degree 13+6+1=20. A Type A q=2 pair then has total multiplicity five; its eight mixed triples total nine occurrences, so each is at most two.

The models add all 28 pair rows and eight point inequalities per half. For each Type A half they also add eight singleton equalities, eight degree equalities and 192 mixed-triple upper bounds. Final row counts are AA 1,113, AB 905 and BB 697. Type A pair zero rows fix 96 formerly allowed block variables per Type A half; effective pools have sizes 1,280, 1,376 and 1,472. No degree20 assertion is imposed on Type B halves.

The complete counting proofs and finite checks are pinned in `eight-eight-redundant-cut-plan/`. Its source, receipt and document hashes are checked before execution. Preparation launches no solver. A separate independent gate is required before root launches the three sequential 120-second, four-worker calls with seeds 2026105501 through 2026105503. Watchdogs, exact assignment checks, both covering verifiers, first-cover stopping and failure handling reuse the reviewed original runner. These are new bounded calls, not retries or extensions of the original campaign. UNKNOWN remains inconclusive; no theorem follows from CP-SAT status alone.
