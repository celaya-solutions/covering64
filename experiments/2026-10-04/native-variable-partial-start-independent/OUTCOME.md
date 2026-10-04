```
Document:    Independent Native Partial-Start Campaign Outcome
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      890c7022bc1ae1744ec938b923863dc2461b00b533839292d3c960feaa29cf2c
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Partial-start campaign outcome

Both authorized runs finished without a cover of at most 64 blocks. The H9
start remained the best raw64 and four-core-admissible64 family in its run. The
H12 start improved to H10 in both categories. Each run retained the separately
verified complete 65-block incumbent.

| Seed | Best raw64 holes | Best four-core-admissible64 holes | Final blocks / holes | Iterations | Wall seconds |
|---|---:|---:|---:|---:|---:|
| 2026104801 | 9 | 9 | 64 / 18 | 39,293,091 | 300.393 |
| 2026104802 | 10 | 10 | 62 / 32 | 42,912,188 | 300.005 |

## Independent runtime checks

`postcheck.json` passed, SHA256
`a6c83b3d60653d09c85650facc367534f94fbfe3aac1655c2125711aa0010920`.
All 18 saved/final paths, representing 7 distinct families, were independently
recounted and checked with both covering verifiers. The first 32 explicit moves
from each run were replayed from the exact initial partial family. Target
coverage, primitive additions/removals, first-lex age fallback, weight-update
policy, and the resulting coverage and core overlaps passed.

Both initial raw/admissible records were saved at step zero with zero mutations
and matched the exact input bytes. The complete initial records matched the
Belic65 incumbent. Both live cardinality ranges were 62 through 64, including
primitive states; the separate 65-block incumbent did not enter those ranges.
All record improvements, final-best links, logs, exit statuses, and manifest
bindings passed. The checker rejected 24 malformed trace controls, two malformed
family controls, and a damaged complete family through both verifiers.

The two runs followed the declared seed order, each with 300 seconds of native
search budget. Neither watchdog fired. Both returned the normal exhausted-run
status, and no extra optimizer was launched by this audit. No relaunch or unused
budget reallocation occurred. No target-cover event occurred, so the actual
first-cover success path was not exercised by this campaign. The pre-run gate
and all frozen producer/audit bindings remain unchanged.

A separate four-worker soft H12 CP run overlapped this campaign. These recorded
wall times are not a controlled performance comparison.

## Interpretation

H10 remains an incomplete family. Four named core caps are diagnostics and do
not establish a global relabel screen. Failure of these bounded heuristic runs
proves no global lower bound or nonexistence result. This audit did not launch
another search or modify any candidate.
