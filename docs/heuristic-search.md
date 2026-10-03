```text
Document:    Heuristic Search for a 64-Block Cover
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      8513cadba93e3cdb9e0a905ec6e71af9d36abbcc3551c4fa94c40a322e650510
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Heuristic search for a 64-block cover

The C++ research tool searches for 64 distinct five-element subsets of 1 through
16. A zero-deficit output is only a candidate until both package and standalone
checkers accept it. A positive deficit or exhausted budget is inconclusive.

## Build and run

```sh
clang++ -O3 -std=c++20 -Wall -Wextra -Wpedantic scripts/heuristic_search.cpp -o experiments/scratch/heuristic-search
experiments/scratch/heuristic-search START.txt SEED SECONDS OUTPUT_PREFIX MODE STEPS_PER_RESTART
uv run covering64 verify OUTPUT_PREFIX-best.txt --expected-blocks 64
uv run python scripts/check_cover.py OUTPUT_PREFIX-best.txt --expected-blocks 64
```

An optional final argument changes the requested size to 65 for finding diverse
starting covers. Finding another 65-block cover does not meet the 64-block goal.
Exit status 0 means zero deficit at the requested size; 1 means the time budget
ended without a cover; 2 means invalid input or an internal error.

The universe uses lexicographic block IDs. Output has sorted blocks and 1-based
labels. The tool rejects repeated labels, repeated blocks, invalid tokens,
overflowing integers, out-of-range labels and wrong block sizes. Every improved
candidate is rebuilt from scratch to audit incremental coverage counts before
being saved. Output files are overwritten at `-best.txt`, while each newly
reached deficit also has its own file. JSONL logs contain seeds, budgets, sizes,
iteration counts, restarts and wall times. Budget cutoffs can change the final
iteration count between runs.

## Search modes

| Mode | Moves and acceptance |
| --- | --- |
| `tabu` | Choose an uncovered triple, evaluate a block insertion against every removable block, and use changing weights on missing triples. |
| `plain` | The same block replacements with unit weights. |
| `point` | One-point replacements, directed point-pair tabu tenure 10 to 12, and protection of new blocks for 5 iterations. |
| `anneal` | Random one-point replacements and repeated cooling cycles. |
| `threshold` | One-point changes within a rotating deficit limit of best through best plus four. |
| `multithreshold` | One-point, two-point and two-block moves, within best through best plus six missing triples. |
| `hybrid` | Annealing with both one-point changes and coordinated point swaps between two blocks. |
| `dispersion` | Annealing with a small secondary penalty for repeated coverage concentrated on the same triples. |
| `regular` | Only two-block point swaps, preserving exactly 20 occurrences per point; input must already have those degrees. |
| `link` | Freeze exactly 19 blocks containing point 16 and search over the other 45 blocks on points 1 through 15. |
| `escape`, `escapeplain` | Exclude a requested number of labeled seed-core blocks, using changing or unit weights respectively. |
| `cap2`, `cap2weighted` | Require every triple multiplicity to remain at most two, using unit or changing weights respectively. |

The `regular`, `link`, `escape` and `cap2` mode families are restricted
searches. None of these restrictions is imposed on the unrestricted model. An unsuccessful run in any such family
says nothing about other families. Link mode first checks that the frozen
blocks cover every triple containing point 16. Escape mode takes a verified
65-block seed and labels as core those blocks whose private triples use all
five labels. Its optional final argument is the minimum number of these core
blocks absent from the candidate (default four). Distance from this labeled
core does not prevent relabelings of the same structure. The cap2 family has
no completeness claim and validates its multiplicity limit at every saved
improvement.

SIGTERM and SIGINT end a run gracefully with an `interrupted` log event. Such
a run did not complete its requested budget. Unwritable output paths fail
explicitly. Each final proposal is audited before a restart or time cutoff.

The most recent tabu variants only bypass tenure for a new best unweighted
coverage record. Newly inserted blocks are protected for five iterations.
The first campaign used weaker tenure aspiration; its exact source snapshot
is retained with its original hash. Source snapshots for every compiled
version are under `experiments/scratch/heuristic-v*.cpp`.

## Recorded evidence

The first independent campaign's best candidate has 64 distinct blocks and
covers 557 of 560 triples. Both checkers rejected it, agreeing that the missing
triples are `(2,7,14)`, `(2,7,15)` and `(7,14,15)`.

- Candidate: `experiments/scratch/heuristic-tabu-2026100301-deficit-3.txt`
- Canonical SHA256: `d6dcfd2f1778f76c90ca67698865f683a44a6b69ddacad8f77cc4ee9021eacdf`
- Independent checker results: `experiments/scratch/heuristic-deficit3-package.json`
  and `experiments/scratch/heuristic-deficit3-standalone.json`
- Invalid-input controls: `experiments/scratch/heuristic-controls-v15.json`
- Cross-check batch: `experiments/scratch/heuristic-all-candidate-checks.json`
  records 154 snapshot pairs agreeing, with no valid 64-block cover.
- Campaign inventory: `experiments/scratch/heuristic-campaigns.json`

The latest build passed seven malformed-input controls, four invalid restricted
seed controls, a known 65-block positive control, an unwritable-path control, a
graceful-stop control and a short cap2 search. These checks do not establish
search completeness or witness existence.

The search remains open. No 64-block covering witness has been verified by
these campaigns. No failure recorded here is an impossibility certificate.

## Reproduction and source provenance

The initial checkout revision was
`582e7ba084e79ed1b7406aa0bc2196b28bab06d7`. The compiler was Apple clang 21.0.0
`clang-2100.3.27.1`, with the optimization and warning flags shown above.
The code uses `std::mt19937_64`. Each log and campaign entry records its seed,
restart budget, elapsed budget, starting file and exact source snapshot hash.
No external mathematical solver is used by this C++ program.

Point tabu and protected-block ideas were informed by Chaoying Dai's 2006
thesis, chapters 5 and 6. See `docs/web-research-2026-10-03.md` for the source
link and scope. Other search variants are experimental adaptations, not
claims about the thesis's measured performance.
