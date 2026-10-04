```text
Document:    Four Case Baseline Integer Pilot from LP Fractionality Ranking
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      5069a52beff49a7eb6c71ad28e0e1052e323556068a917db45dce6ea8721e1cd
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Result and scope

All four baseline searches ended UNKNOWN after their 60-second limits.
No candidate was returned. These outcomes are inconclusive and supply no
infeasibility result.

| First-link case | Status | Elapsed seconds | Seed |
| --- | --- | ---: | ---: |
| cycle-069 | UNKNOWN | 60.005141 | 2026103101 |
| cycle-111 | UNKNOWN | 60.005128 | 2026103102 |
| matching-029 | UNKNOWN | 60.005213 | 2026103103 |
| matching-030 | UNKNOWN | 60.005059 | 2026103104 |

Each run used two workers. The cycle pair ran together, followed by the
matching pair, with at most four solver workers active. OR-Tools was
`9.15.6755`. The nominal total search budget was 240 solver-seconds;
reported elapsed times include a few milliseconds of stopping overhead.

The cases are the two lowest fractional-block-mass LP solutions in each
branch, as recorded in the adjacent `four-seven-lp-primal-inspection` folder.
This ranking is a search heuristic. Each CP model contains exactly the
frozen audited lifted four-sevenfold base plus seven selected first-heavy-link
blocks fixed to one. There are 4,768 Boolean variables and 4,277 rows.
No new feature cuts, fixed double pattern, group-invariance restriction,
objective, or hints were added.

# Model preservation

`check_model.py` independently parses the full and base protobufs, checks
each of the seven added equality rows, removes those rows, and compares
every remaining proto field. All four comparisons pass. It also checks
the saved base and full-model hashes. `model-audit.json` records the checks.
This establishes preservation of the frozen model, not an integer proof.

The runner loads the base directly from the saved first-link LP screen and
checks its hash against the primal-inspection input manifest. It obtains
the seven fixed block IDs from the preserved primal results. All block
variables keep their global lexicographic IDs; point labels are 1-based.

Any returned candidate would be required to have 64 distinct blocks and
pass both the package verifier and frozen standalone `check_cover.py`.
None of these four solver runs returned a candidate to check. The separate
LP inspection checked all 158 rounded partial candidates through both
verifiers before these cases were selected.

# Evidence and replay

`pilot.json.gz` preserves all four run metadata records, exact parameters,
source snapshots, solver summaries, model-preservation audits and hashes
for full models and logs. `result.json` provides a compact summary. Full
base models, fixed-link models and logs remain under the ignored directory
`experiments/scratch/four-seven-first-link-cp-20261003`, with one subdirectory
per representative. Each metadata record gives its source revision and
input artifact hashes.

Archive SHA256:
`0b1c9bc276c3723672c8f4e9276c33b6f0a1e2c3c0df1ef19f41464a91d11bc9`.

Recheck a saved model without rerunning the solver:

```sh
uv run python experiments/2026-10-03/four-seven-first-link-cp/check_model.py \
  experiments/scratch/four-seven-first-link-cp-20261003/cycle-069
```

The frozen baseline permits comparison with later models containing audited
feature cuts; it contains none of those later cuts.
