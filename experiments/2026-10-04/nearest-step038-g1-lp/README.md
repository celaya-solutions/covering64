```
Document:    Fixed Cycle Graph Diagnostic for Nearest Tuple 038
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      8f7b092ba3a1bd895950eba0bfc015016ef2ed97c04668ec0d21b820bedcda09
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

The one authorized elastic LP returned OPTIMAL with objective
**8.024244815488677**, using one worker and 0.139582 solver seconds under a
10-second cap. There was no separate feasibility solve and no integer search.
The tuple's previous all-graph elastic score was 5.966796868079938; these scores
measure different feasible regions and must not be mixed.

This diagnostic fixes the only first-link-registry-open hub graph for nearest
master step 038. In pair order (4,8), (4,12), (4,16), (8,12), (8,16), (12,16),
the exact pair targets are (5,6,6,6,6,5). All other model rows and all 1,200
ordinary columns retain the audited regular four-sevenfold definition. The
697 original rows were directly constructed and separately rebuilt using the
pinned-profile checker, with precisely those six hub-pair bounds tightened
to equalities before comparison.

The frozen exact-arithmetic helper recovered a signed certificate with 527
nonzero integer row weights and denominator 1,000,000. Independent replay
against the newly reconstructed rows gives right side 8,024,250 and Boolean-box
maximum 123, hence a positive exact gap **8,024,127 / 1,000,000**. This excludes
the fixed tuple's completion under graph 1. It is not an all-graph search cut
or an exclusion of nearby heavy tuples. Together with the separate registry
exclusions of its other five hub graphs, this particular tuple has no
64-block completion; it remains a possible starting point for changing the
heavy tuple.

The saved numerical primal was replayed with exact rational representations
of its binary floating-point values. Its elastic residual is below
8.024244816. No exact fractional feasible witness or covering witness was found.

`seed.txt` stitches the same original 36 ordinary blocks to the selected
28 heavy blocks. Both independent cover checkers agree that it contains
64 distinct blocks and 13 holes. It is a search seed, not a cover. The manifest
records the exact retained ordinary blocks and heavy block IDs.

`run.py` refuses to repeat this run in its existing raw directory.
`manifest.json`, `model-audit.json`, `dual.json`, `dual-audit.json`, `result.json`
and `receipt.json` bind sources, inputs, solver version and results. Raw
original and elastic models, all variable values, numerical primal and dual,
full solver log and frozen source remain in
`experiments/scratch/nearest-step038-g1-lp-20261004`. `files.json` binds the
compact evidence and `raw-files.json` binds those ignored raw artifacts.
