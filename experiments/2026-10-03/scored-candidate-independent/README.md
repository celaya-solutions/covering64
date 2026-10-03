```
Document:    Independent Scored Candidate Structural Screen
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      4b4358fcd0fc6b47c45b8bf12f0227f9498138c42f7267d20aa6864e6b928b55
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent scored-candidate screen

`h13-report.json` independently recounts the scored-qualified native candidate
`search-qualifying_improvement-21-h13.txt` from the `penalty-2026100363` run.
The witness has 64 distinct blocks, all point degrees 20, and thirteen holes.
The package verifier, standalone verifier, and raw subset recount agree.
Candidate SHA256: `95047e6f69ba507ccfee3c4cb0ccb809e78ed232d5178453d403e9b71293c765`.

Its heavy triples and repeated outside hubs are:

| Triple | Multiplicity | Hub |
|---|---:|---:|
| 1,2,3 | 7 | 4 |
| 5,8,11 | 7 | 10 |
| 9,13,16 | 7 | 12 |
| 10,14,15 | 6 | none |

The heavy triples are disjoint and the hubs are distinct, but hub 10 belongs
to the exact-six triple (10,14,15). This violates the proven requirement that
all heavy-triple hubs lie outside all heavy triples. The exact-six triple has
no repeated hub, so n6=1, n7=3, h6=0 and the refined count is 15. Passing this
count does not cure the incompatible point roles.

The complete-coverage pair lower bounds also expose current repair needs:

- General pairs (4,5), (5,12), (8,16), (10,16) have multiplicity four, below five.
- Internal heavy pairs (10,14), (10,15) have multiplicity six, below seven.
- Hub/anchor pairs (10,11), (9,12) have multiplicity five, below six.

These are deficits in a partial witness. They are not a nonexistence result for
its future descendants. Any full completion must remove the hub/anchor conflict
and repair the applicable pair deficits.

Unlike the earlier h9 seed, this candidate's fixed-family necessary pair-row
bounds do pass. The row for normalized hub 4 is 24; all other rows are 24 to 26,
within budget 28. Passing those rows does not prove outside completion exists.
All row values and all 120 pair counts are saved in the report.

`check.py` is a reusable independent snapshot screen for the continuing search.
It uses frozen independent hub-audit utilities, never the production heuristic
metrics, and records checker, utility, verifier, and candidate hashes. The
h9 positive control passes the explicit heavy/hub topology tests (while remaining
a partial witness); the h6 negative control correctly fails hub distinctness.
Additional snapshots should be saved under new report names without overwriting
these evidence files.

Run from the worktree root:

```sh
uv run python experiments/2026-10-03/scored-candidate-independent/check.py CANDIDATE OUTPUT.json
```

The meaning of native scored qualification is limited to the metrics included
in that score. It does not imply all known necessary structural conditions pass.
