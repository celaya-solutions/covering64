```text
Document:    Point Star Repair Pilot
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      c55b92e3671ad742b45284ad4fddce3571280f1f1f7ccac17b0211859c48b9be
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Point-star repair pilot

The four bounded runs found no improvement. Each returned only the original
64-block, three-hole candidate. No cover or useful escape seed was found.

## Search and scope

Remove every original block containing point 2 or point 15; fix only the other
blocks. Each model has all 4,368 lexicographically ordered block variables,
exactly 64 selected blocks, and 560 exact hole indicators. No degree, heavy
profile, core overlap, pool, or symmetry constraint was added.

Point 2 removes 19 blocks and retains 45, leaving 169 triples uncovered before
repair. Point 15 removes 21 and retains 43, leaving 175 triples uncovered.
Any full cover needs at least 19 blocks through each point, from the recursive
link bound ceil((15/4) * ceil(14/3)) = 19. Therefore a full point-2 repair would
necessarily use all 19 replacement slots through point 2. Point 15 has two
additional slots. This consequence is not imposed as a model constraint.

The objective is `(removed_count + 1) * holes + old_star_blocks_reselected`.
It gives strict priority to fewer holes, then favors changing more star blocks.
The complete original three-hole state is supplied as a hint. All improving
objective callbacks are saved and checked.

These are two conditional retained-block neighborhoods, run with two seeds each.
Focused scheduling is new in the reviewed local record; the reachable moves
already fit within larger prior LNS neighborhoods. Of 316 saved LNS attempts,
none removed exactly a whole point star. Thirteen nonexact attempts contained
27 complete point stars and stayed at three holes; 20 exact attempts contained
42 complete stars and returned UNKNOWN. `prior-removal-audit.json` records the
input hashes and distinguishes attempts from star occurrences.

## Gate and checks

The independent checker reconstructs both models from standard combinations
and compares their complete deterministic protobuf encodings. The two models
have 4,928 Boolean variables and 1,166 / 1,164 rows, including all 1,120 reified
coverage rows, exact cardinality, and the specified retained-block rows. It also
checks the objective, hints, source/dependency hashes, and seed using fresh
triple unions and both covering verifiers. No optimization ran before this gate.

Every saved candidate was independently recounted from its block list and
checked with the package verifier and standalone `scripts/check_cover.py`.
The verifiers correctly report these three-hole candidates as incomplete.
The runner records exact additions/deletions relative to the initial state.
Profiles are computed after each run and never restrict the search.
A separate `postcheck.py` readback confirmed all four states, move differences,
objectives, profiles, retained blocks, and bound hashes without rerunning search.

## Results

| Point | Seed | Budget | Status | Best holes | Changed blocks |
| --- | --- | --- | --- | --- | --- |
| 2 | 2026104001 | 30 s, one worker | FEASIBLE | 3 | 0 |
| 2 | 2026104002 | 30 s, one worker | FEASIBLE | 3 | 0 |
| 15 | 2026104003 | 30 s, one worker | FEASIBLE | 3 | 0 |
| 15 | 2026104004 | 30 s, one worker | FEASIBLE | 3 | 0 |

Total solver time was 120.016298 seconds. Every objective bound was zero.
Each run saved only its initial state, with holes `(2,7,14)`, `(2,7,15)`, and
`(7,14,15)`. Its five disjoint heavy triples have multiplicities 7,6,7,7,7,
so the existing forbidden-profile screen remains positive. There were no
improved partials. Standard error was empty. These bounded outcomes do not
exclude a better repair or any unrestricted cover.

## Reproducibility

`metadata.json` binds source, dependency, input and model hashes, source revision,
Python and OR-Tools versions, seeds, budgets, and worker counts. `gate.json`
binds the independent check; `summary.json` and the per-run folders contain the
results, witnesses, audits, and profiles. Large model files and solver logs
remain outside Git under `experiments/scratch/point-star-repair-20261004/`.

Preparation: `uv run --no-sync python experiments/2026-10-04/point-star-repair/run.py prepare`.
Gate: `uv run --no-sync python experiments/2026-10-04/point-star-repair/check.py`.
Run: `uv run --no-sync python experiments/2026-10-04/point-star-repair/run.py run`.
The existing prepared and completed directories intentionally prevent rerunning
this receipt in place. No repository-wide files or frozen earlier evidence were
edited. Scoped Ruff validation passed; the parent owns repository-wide checks.
