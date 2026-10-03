```text
Document:    Bounded Six-Removal Core Extension Scan
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      5090444fac1198aa6dd43176b0f632b5f1849a31ec858df134ab3d3cda87b37a
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Bounded six-removal extension scan

All 55 one-block extensions of removal set [1,22,23,25,29] were scanned,
reducing to 33 distinct classes under the certified 60-element core-preserving
subgroup. Each retains 54 core blocks and allows 10 additions for a 64-block
cover. Every resulting exact feasible dual is at most 10; this LP scan excludes
none of these 33 classes and does not establish that any is feasible.

The smallest exact dual is 9,968,749/1,000,000 = 9.968749, for removal set
[1,10,22,23,25,29]. The sorted candidate file gives each explicit retained-core
list, 0-based lexicographic Universe block IDs, removed 1-based core indices,
and the exact rational dual. Each dual was checked against independently
enumerated possible 5-blocks before output.

The case family is restricted to one-block extensions of the specified parent.
No claim covers all six-removal sets. `scan.json.gz` contains all raw duals and
source provenance. `lp-candidates.json.gz` contains all 33 candidate neighborhoods
in ascending dual-bound order for exact search. `summary.json` records hashes
and scope. Raw logs and source snapshots are outside Git in
`experiments/scratch/core-six-scan-20261003/`.

The exact duals also give small, complete candidate pools. Reconstructing and
checking the weights gives dual 319/32 for the best case, 739/74 for the next,
and exactly 10 for the remaining 31. A ten-block completion needs every added
block to have dual load at least B-9: if one block had smaller load, the other
nine each contribute at most one and their total would fall below B. This
reduces the 33 pools to between 42 and 80 blocks; the first two have 51 each.

`dual-reduced-candidates.json.gz` contains the exact reconstructed weights,
integer cutoff, and complete eligible-block IDs and lists. The standard-library
script `scripts/reduce_core_candidates.py` rebuilds every possible block's
load and reproduces that file exactly. For cases with B=10, every added block
must be tight and each positive-weight triple must be covered exactly once.
These reductions are complete for each specified retained-core neighborhood;
they do not exclude the neighborhoods on their own.

Reproduce the scan with:

```sh
uv run python scripts/scan_core_extensions.py --parents '[[1,22,23,25,29]]' --output experiments/2026-10-03/core-six-scan --raw experiments/scratch/core-six-scan-20261003
```

The bounded scan used deterministic parent/extension ordering, GLOP defaults,
and no time limit or random seed. Versions, source hashes, base revision, and
elapsed time are recorded in `summary.json`. Feasibility must be settled by an
actual verified cover or a separately checked obstruction.
