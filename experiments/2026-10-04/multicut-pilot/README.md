```
Document:    Single Three-Minute Fourteen-Cut Pilot
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      c3dfe24274d1cce984325b8ba866310e490c723b27ef68f15eea52dd483d7549
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Single three-minute fourteen-cut pilot

Exactly one 180-second, one-worker cycle run used native v1.4.1, seed
2026104051, `--cut-guide --cut-weight 10`, and the frozen previous ten-hole
best. The root's embedded-source review, separate runtime review, optimized
build and sanitizer controls all passed before launch. No repeat ran.

The process finished normally after 180.001 native seconds (180.432684 wrapper
seconds), with 53,830,825 proposals, 107 restarts and 126 real cache evictions.
Stderr was empty. Native exit 1 means the normal no-cover result. The wrapper
was not forced to terminate.

## Results

| Saved role | Holes | Base score | Full score | Cut penalty | All fourteen cuts pass |
| --- | ---: | ---: | ---: | ---: | --- |
| Initial seed | 10 | 82 | 212 | 130 | No |
| Raw best | 10 | 82 | 82 | 0 | Yes |
| Score best | 10 | 82 | 82 | 0 | Yes |
| Actual terminal state | 25 | 173 | 173 | 0 | Yes |

Raw best and score best are the same new saved family, found at 1.00881 seconds
and proposal 246,954. They have zero unsupported triples, 602 admissible
ordinary blocks under the lookahead oracle, and zero heavy excess. The terminal
state has zero unsupported triples and 680 admissible ordinary blocks. None is
a covering witness; all have positive hole counts. The best hole count remains
ten, and the best verified full cover remains size 65.

The new ten-hole witness is frozen as `cycle-raw-best.txt` with SHA256
`4382c01b0ebc7c5b9d6a2c38314ab58ea35962350052d521fd1d103d16c1d6fe`.
The identical best/score-best copies and their sidecars, plus the actual
terminal state and its sidecar, are retained here for inspection.

## Complete saved-state audit

`audit.py` checked all 54 saved states and 16 logged operations against the
independent Python score and lookahead oracle. Every state ran through both
the package verifier and standalone `scripts/check_cover.py`, and all outputs
are saved. This includes the actual terminal state added by v1.4.1.

The audit independently reconstructs all fourteen cut LHS values, maximum
violation, ceiling and weight, full score, complete admissible/unsupported
sets, point degree 20, all four seven-block heavy groups, their outside-point
degree profiles, and pair/triple multiplicity profiles. It checks move
inventories, reported before/after scores, ordinary-move heavy-sum invariance,
rollback and the best-record orderings. Thirteen damaged sidecar fields were
rejected. See `audit.json` for bindings and every snapshot hash.

`manifest.json` binds source, binary, input catalog, seed, cut bundle, both
independent gates, prior native audit, build record, exact command and source
revision. `result.json` binds the complete stdout/stderr and native summary.
Large logs, all intermediate witnesses, their sidecars, source/input snapshots,
and both-verifier outputs remain in the ignored
`experiments/scratch/multicut-pilot-v1.0.0/` directory.

## Follow-up LP diagnostic

Passing the fourteen inequalities is only a finite necessary screen. The new
best was immediately checked by the separately reconstructed full six-graph
LP in `../multicut-best-lp/`. It is still infeasible: the exact signed-row
certificate gap is 8269/500 = 16.538. Its numerical elastic objective is
16.68585525272344, worse than the prior seed's 12.64569999478813. Thus the guide
moved beyond the stored cuts without improving raw holes or obtaining an
LP-completable heavy tuple. No CP solve or additional native run followed.

The official 109 first-link exclusions and 149 open representatives remain
unchanged. This construction experiment supplies no unrestricted lower bound.
The narrow Ruff checks passed; global checks and Git integration belong to the
coordinating agent. Existing launcher and audit outputs are frozen and refuse
reuse of their output directories.
