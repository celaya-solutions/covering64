```text
Document:    Affine Circle Incidence Relaxation Pilot
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      d46498220b8331d30353105fe11a4c17719d0639e6d9773ba8af8b13b3ab0447
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Result and scope

The one approved 60-second run returned **UNKNOWN**, with no candidate.
This is inconclusive. It proves neither feasibility nor infeasibility in the
restricted pool, and gives no unrestricted lower bound for C(16,5,3).

The model is a necessary relaxation of the original 48-circle plus 240-extension
pool. All 288 Boolean variables represent selected blocks and are ordered by
their global lexicographic block IDs. Its 69 rows are:

- One row selecting exactly 64 blocks.
- Twenty rows requiring at least one extension of each affine line.
- Forty-eight circle rows: 10*x_C plus the sum of selected extensions covering
  a triple of C is at least 10.

A retained circle satisfies its own row. A deleted circle has ten triples to
cover, and each extension covers at most one. This makes its incidence row
necessary. Repeated coverage of the same triple still counts multiple times,
so these rows do not establish full coverage. There is no imposed number of
circles or extensions, fixed block, incidence profile, or symmetry constraint.

The root's independent gate constructs each circle row by summing its ten
actual triple-coverage rows across the complete pool. All 69 rows and variable
domains match exactly, and seven damaged models are rejected. This avoids
depending on the builder's intersection-count calculation.

## Frozen run

- Seed: 2026103984; requested budget: 60 seconds; one worker.
- OR-Tools: 9.15.6755; solver wall time: 60.002797 seconds.
- Reported conflicts: 4,566,512; branches: 28,224,435.
- Model SHA256: `dc4ec15af0972670faf5a1562c4aac184d16c1df51b53ca341f27ced02c91b37`.
- Independent gate SHA256: `945cfff219272d0da8deacad63c303fb707e745cd86c6ea79e7810db08e6c985`.
- Runner SHA256: `d5efb9c60badfaf46bfaa104694068b6479e006fa336d00e22b29d0347aab93d`.

`check_result.py` reads the saved parameters and response, verifies their exact
agreement with the result, checks all artifact hashes, and rejects nine damaged
result controls. No candidate was available for covering verification. The
runner would require package and standalone agreement on every missing triple
before reporting any feasible relaxation candidate as an actual cover.

Raw source snapshots, pool, model, parameters, solver log and response remain
outside Git in `experiments/scratch/affine-circle-incidence-relaxation-20261003/`.
Tracked manifests record the source revision and hashes. The model and run
directories are immutable; the builder and runner refuse to overwrite them.
No repeat of the unchanged pilot was made.
