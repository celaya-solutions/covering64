```text
Document:    Fixed-g1 Nearest Master Continuation
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      6d4a54372f11896fee1f8c6d25f6a594fa79e57218f64d6bc9ec0f65e90f5f98
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Fixed-g1 nearest-master continuation

The one authorized continuation completed within its frozen budgets. It made 42
master proposals: 41 OPTIMAL and one FEASIBLE, with no UNKNOWN outcomes. All 42
selected 28-heavy-block patterns were six replacements from the frozen baseline.
The registry rejected 16 proposals before completion LP evaluation. The remaining
26 completion LPs were OPTIMAL, but none improved the saved score
**7.52051548546158**. The best fresh score was 9.141496147218286 at proposal 5.
There was no numerical zero, exact fractional feasibility, or covering witness.
No new stitched integer candidate was needed because there were no improvements.

The campaign used 115.15139658120461 combined solver seconds and
130.76688487501815 wall seconds, then stopped at the conservative budget guard.
Limits were 50 admitted LPs, 100 master proposals, 120 combined solver seconds,
160 wall seconds, one worker, five seconds per master and one second per LP.
Presolve was off, and proposal seeds were 2026104070 plus the zero-based proposal
index. UNKNOWN would have been recorded and followed by the next seed; this path
was not encountered during this campaign.

The frozen initial master was the previous 1,977-row master plus exactly two
checked diagnostic rows: one g1 cut with exact gap 337849/25000 and one seven-block
cycle-028 nogood on global IDs [10,11,15,27,35,46,69]. Thus the initial model had
276 Boolean variables, 605 heavy-family rows, 353 broad cuts, 1,001 conditional g1
cuts, and 20 g1 registry nogoods, for 1,979 rows. Its objective stayed
28 minus overlap with the frozen baseline; there was no distance constraint or
radius. All four links were registry-checked before each admitted LP.

The run generated 26 new positive exact g1 cuts and 18 new g1 registry nogoods,
ending with 1,027 g1 cuts and 38 nogoods. These remain separate from the unchanged
353 broad cuts. The graph-specific completion rows use g1 excesses
[0,1,1,1,1,0] and hub-pair targets [5,6,6,6,6,5]. Their family hash is
`2d14cafb6016203749ea63052913afc4af28800daaf5fc62ec6c459fc43aac32`.

The independent pre-run gate passed in
`../g1-nearest-master-continuation-independent/audit.json`. Independent postcheck passed: `../g1-nearest-master-continuation-independent/postcheck.json` (SHA256 `12bf69e66a15df228a7c414da1a28d0b99d1093d2f7684fd20c2c0fbf4a72a1f`). It rebuilt all 42 masters, checked their assignments and registry transports, replayed all 1,027 initial/new exact g1 planes and 38 final nogoods, and rejected seven damaged controls. All exact-cut and nogood receipts are preserved in the deterministic
250,237-byte `learned-proofs.json.gz` archive. Its 27 raw text files were restored
in memory and matched to their original SHA256 values. `archive.py` and
`archive.json` describe how to restore those exact bytes. Full native models,
parameters, responses, logs, registry transports, and numerical vectors remain
under the ignored scratch run folder; `result.json` indexes their hashes.

These results concern the fixed-g1 search only. A bounded sample is not a
neighborhood exhaustion, an unrestricted infeasibility proof, an elastic-optimum
theorem, or a global covering lower bound. Numerical solver statuses alone do not
supply an independently checked mathematical proof.
