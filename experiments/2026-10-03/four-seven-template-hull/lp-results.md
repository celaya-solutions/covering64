```
Document:    Bounded Whole-Template-Hull LP Results
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      5550f53fab7e5b24540e3ceb8b44114190ee26df7caa86c6dd4fb9c41072a4cd
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Both whole-catalog cases remain numerically feasible

The two LPs using the complete surviving-link catalogs returned GLOP OPTIMAL.
Neither stored block vector is integral. No covering candidate or new exclusion
was obtained. These runs concern the two case-wide models; they do not screen
each fixed first-link representative separately.

The catalogs remain frozen at the original 100 checked exclusions. Later
blossom or other exclusions are not incorporated into these inputs.

| Case | Variables | Rows | Solve seconds | Fractional block variables | Positive template weights |
| --- | ---: | ---: | ---: | ---: | ---: |
| Cycle | 104,848 | 4,550 | 6.756837 | 444 | 98 |
| Matching | 61,576 | 4,550 | 2.838938 | 453 | 97 |

Each case had a 60-second total solver budget. Construction time was recorded
separately: about 0.130 and 0.076 seconds. No phase-one solve or infeasibility
certificate attempt was needed. Solver version, source revision, input hashes,
verifier hashes, command, budgets, logs, and full primal vectors are saved.

The independent stored-vector audit uses exact rational arithmetic on the
binary floats and checks every row and variable bound. It finds zero domain
violation and maximum row residuals approximately `6.81219e-13` for cycle and
`8.66140e-13` for matching. These small nonzero residuals qualify numerical
feasibility only; the vectors were not reconstructed as exact primal witnesses.

The first 4,368 block variables have fractional masses about 62.849789 and
62.602524. Only five and six block values, respectively, meet the one-half
threshold. Neither vector is close to a zero/one selection of 64 blocks, so
neither was treated as a candidate. The runner's candidate path was separately
tested with an incomplete 64-block integer control through both package and
standalone verifiers.

## Evidence

- `runner-check.json`: pure certificate arithmetic, metric, and candidate-dispatch
  controls; no solver calls were used for those controls.
- `lp-result-summary.json` and `lp-run.log`: the saved numerical outcomes.
- `lp-primal-audit.json` and `.log`: independent complete row/vector recounts.
- `run_lp.py`: bounded runner requiring a successful independent audit of the
  exact prototype manifest before it can solve.
- `check_primal.py`: standard-library-only stored-vector audit.

Large run artifacts remain in
`experiments/scratch/four-seven-template-hull-lp-20261003/`. Each case has its
raw GLOP log, result, and full `primal.json.gz`. The run directory also preserves
the exact runner, prototype manifest, independent audit, verifier sources, and
metadata.

The runner SHA256 is
`c6b67b22660707c701ae038db497e81fded3c647e9f1978873b5e27da573afcf`.
The cycle primal archive SHA256 is
`f709c5c46efbfd2b8879f850d84a80545071d6fa3395692972dbdec0c0981ea4`.
The matching primal archive SHA256 is
`a0ad8f77f33c2cb29a57392a37a123b92d645d4cc390cd56d80b1363b0e8f7e8`.
The independent primal audit SHA256 is
`1a53d0c846ee20dddcbcba38dbd99969f74d07fbead137329153932c106fe5a7`.

The header hash covers the body after the header fence, including its initial
blank line.
