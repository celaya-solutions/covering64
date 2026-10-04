```text
Document:    Primal Inspection of 158 Remaining First-Link Cases
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      00b6765af12db8030522495836c8d49134e9917365816b8138f4fb6cca643387
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Findings

All 158 remaining fixed-first-link LPs were solved again. Every rerun was
numerically feasible, but none had integral block variables. Each LP's
top-64 rounded block set was checked by both the package verifier and the
standalone verifier. All 158 are partial candidates, with 92–135 missing
triples. No cover was found.

The batch contains 102 cycle cases and 56 matching cases. Each has 4,768
continuous variables in [0,1] and 4,277 rows: the audited lifted base plus
seven fixed first-link block rows. The source is the frozen full first-link
screen, with no new constraints or objective. All GLOP statuses were OPTIMAL
with zero objective. This is numerical LP feasibility, not an exact rational
witness or an integer construction.

The maximum absolute row-bound violation was `6.0254023992456496e-12`; no
variable-bound violation was found. The sum of reported LP elapsed times
was 35,094 milliseconds. Every case was within the `1e-7` qualification
tolerance. OR-Tools was `9.15.6755`; each LP had a 10-second limit.

# Ranking and rounding

For the first 4,368 block variables, define fractional mass as
`sum(min(clamp(x,0,1), 1-clamp(x,0,1)))`. A variable counts as fractional
when `1e-7 < x < 1-1e-7`. Auxiliary double-variable fractionality is reported
separately and does not enter the block ranking. The primary order is
fractional mass, then fractional count, rounded deficit, and representative
ID. A separate count-first order is retained in `summary.json`.

Fractional block counts range from 369 to 411; masses range from
`54.39948386073712` to `56.999999999999964`. There are only 7–8 near-one block
variables per case. Nearest-half rounding selects 7–17 blocks, so it does
not supply 64-block candidates. The tested top-64 method selects the 64
largest raw block values, breaking ties by global lexicographic block ID.
It is a search heuristic and does not preserve model constraints.

| Representative | Fractional mass | Fractional blocks | Missing triples after top-64 rounding |
| --- | ---: | ---: | ---: |
| cycle-069 | 54.399484 | 401 | 116 |
| cycle-111 | 54.646148 | 390 | 95 |
| matching-029 | 54.765701 | 387 | 110 |
| matching-030 | 54.773080 | 387 | 113 |

These are the two lowest-mass representatives in each case. They were
selected for the separately recorded baseline CP pilot: 60 seconds per
case, two workers, with at most two cases running together. That pilot adds
only the seven fixed link blocks to the frozen lifted base. Its artifacts
are in the adjacent `four-seven-first-link-cp` folder.

The count-first leaders are `cycle-012` (369 fractional blocks) and
`matching-113` (376). The smallest rounded deficit is 92 at `matching-097`.
These alternative metrics are recorded for comparison; they are not evidence
of integer feasibility or a guarantee of search difficulty.

# Evidence and replay

The ignored scratch folder is
`experiments/scratch/four-seven-lp-primal-inspection-20261003`.
Each representative directory preserves all 4,768 raw floating-point values
in `primal.json.gz`, the rounded candidate, both complete verifier outputs,
and a summary. The 158 compressed primal files total 1,045,153 bytes.
Copies of the input base models, row arrays, full-screen results,
representatives, metadata and source snapshots are also retained there.

`evidence.json.gz` is the compact durable archive. It stores all result
summaries, the selected 64 block IDs for every candidate, both ranking
orders, frozen source snapshots and hashes for all full scratch artifacts.
`summary.json` holds aggregate metrics and the chosen pilot cases. The
recorded inputs select exactly the 158 previously LP-feasible cases; the
100 independently excluded cases are not rerun.

Archive SHA256:
`eed3f646217d99fa5dfaf0ea621744283ebef993c0716706bdc350025576fec5`.

Reproduce the primal batch into a new scratch directory:

```sh
uv run python experiments/2026-10-03/four-seven-lp-primal-inspection/run.py \
  experiments/scratch/four-seven-link-lp-full \
  --output experiments/scratch/four-seven-lp-primal-inspection-repeat \
  --seconds 10
```

The ranking describes these saved numerical basic solutions. A solver change
or a different feasible LP solution can change it without changing the
underlying integer problem.

# Independent primal spot checks

`independent_spot_check.py` rechecks five saved vectors: cycle-069, cycle-111,
matching-029, matching-030 and matching-097. It uses exact rational arithmetic
on the stored binary floating-point values for all 4,277 rows, independently
recounts lexicographic rounding and missing triples, and verifies saved hashes
and fractionality metrics. All five audits passed in `independent-spot-check.json`.
Their small nonzero row residuals remain numerical evidence, not exact feasible
primal witnesses. Every rounded candidate is incomplete.
