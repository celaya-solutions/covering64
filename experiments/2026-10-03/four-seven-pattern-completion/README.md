```text
Document:    Block Completion Tests for Two Fixed Double-Triple Patterns
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      0209645bb050c5f32c9ba774dac8aaa85e3be2e0cd8d3e9651565634830d35dd
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Results

Neither of the two saved 44-double-triple patterns produced a 64-block cover.
Both full block-completion linear relaxations were numerically feasible.
The cycle integer search timed out. CP-SAT reported the matching model
infeasible, without a separately checked integer proof.

| Pattern | GLOP linear relaxation | CP-SAT | Search budget |
| --- | --- | --- | --- |
| Cycle | OPTIMAL, objective 0, 130 ms | UNKNOWN, 120.005463 s | 120 s, 2 workers, seed 2026103001 |
| Matching | OPTIMAL, objective 0, 116 ms | INFEASIBLE, 59.005908 s | 120 s, 2 workers, seed 2026103002 |

Numerical LP feasibility is not an exact rational witness. The matching
solver outcome is not an independently checked theorem. Neither result
establishes a global lower bound or excludes the full four-sevenfold branch.

# Exact scope and model

The inputs are the independently recounted `cycle-pattern.txt` and
`matching-pattern.txt` in the adjacent `four-seven-double-patterns` folder.
Each supplies 44 distinct eligible triples. Build the complete normalized
regular 64-block four-sevenfold model for its case, add the audited
400-double-variable lift, then fix **all 400** double flags to the supplied
pattern: 44 flags to one and the other 356 to zero.

The resulting models have 4,768 Boolean variables and 4,670 linear rows.
The first 4,270 rows are the full lifted branch model; the final 400 rows
fix the flags. There are no additional group-invariance or first-heavy-link
restrictions. Global block-variable order and 1-based labels are preserved.
Both models pass `model.validate()`.

`check_flags.py` separately parses each frozen model with the protobuf parser,
reconstructs all eligible triples using `itertools`, and checks all 400 fixing
rows, all variable names/order/domains, and the frozen source/input/model
hashes. Both audits pass. Its scope is the fixing suffix and variable order;
the earlier branch and lift audits remain the evidence for the base rows.

# Evidence

The source revision was `bcf4fcc1b998d11227cd04145470f2ace79b71e2` with
uncommitted source snapshots preserved. OR-Tools was `9.15.6755`.
The LP helper snapshot was version 1.0.1, SHA256
`1727af53a4106373c492ad3d1eddbac921565dd154101c28c0a3487cd539faec`.
The LP stage had a 10-second budget. Both cases entered the integer stage
immediately after the numerical LP completed; no phase-I certificate was
needed or produced.

`cycle.json.gz` and `matching.json.gz` retain the exact patterns, metadata,
parameters, source snapshots and solver summaries. `result.json` records
their hashes. Full model protos, row arrays and solver logs remain under
the ignored scratch paths recorded in the archives, with hashes retained.
The raw 400-row audit reports are `cycle-flags-check.json` and
`matching-flags-check.json`.

| Case | Model SHA256 | Archive SHA256 |
| --- | --- | --- |
| Cycle | `1cbcf71778aab63d407ff0a65ebcc51b2e8465854762d490fe26359fcc60a05f` | `500376a3a9fe156290501f37a8a37fb41dcf3c71d9267f9b758af58940bcf136` |
| Matching | `ea76d4b0b3b384d5fe76e7751690ef04afa309b8e7f677f96eadbc05f8e5e765` | `ad527c675badea100ae7a169353762b313e17babd677d4c6c31d92aed2deb20c` |

Recheck the fixing rows from the repository root:

```sh
uv run python experiments/2026-10-03/four-seven-pattern-completion/check_flags.py \
  experiments/scratch/four-seven-cycle-pattern-completion-20261003
uv run python experiments/2026-10-03/four-seven-pattern-completion/check_flags.py \
  experiments/scratch/four-seven-matching-pattern-completion-20261003
```
