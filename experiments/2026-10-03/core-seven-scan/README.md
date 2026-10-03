```text
Document:    Bounded Seven-Removal Core Extension Scan
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      9f1e9ee2145b0092f51e0506df63e9c4f50223d64da01cbb25b9d5100f9d896f
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Bounded seven-removal extension scan

One-block extensions of the three lowest-bound six-removal representatives
produced 100 distinct classes under the certified 60-element core-preserving
subgroup. Each retains 53 core blocks and permits 11 additions for a 64-block
cover. Every exact feasible LP dual is at most 11; the LP scan itself excludes
none of these classes and does not establish feasibility.

The three parent removal sets were:

- [1,10,22,23,25,29]
- [1,10,22,23,35,37]
- [1,5,22,23,25,29].

All 54 possible extra removals were considered for each parent, with duplicate
subgroup classes removed. This is a restricted three-parent family, not every
seven-removal subset of the 60-core.

The best reconstructed exact dual is 76/7 for removal set
[1,3,10,22,23,25,29]. Thirty classes have dual exactly 11; seventy have a
smaller dual. Every dual exceeds 10. Any completion therefore needs exactly
11 additions, and each added block must have dual load at least B-10, because
the other ten have load at most one. Rebuilding all 4,368 block loads gives
complete candidate pools of 46 to 137 blocks. These reductions preserve every
possible completion in each specified neighborhood.

## Evidence

- `scan.json.gz`: all raw duals, explicit parents, core, subgroup generators,
  source hashes, base revision, solver versions, and elapsed time.
- `lp-candidates.json.gz`: all 100 neighborhoods with explicit retained blocks.
- `dual-reduced-candidates.json.gz`: checked reconstructed rational duals and
  complete eligible-block IDs/lists.
- `verification.json`: standard-library scan audit, artifact/source hashes,
  and scope. The audit independently closes the group, regenerates every
  extension class, and checks each dual against all possible blocks.
- Raw logs and source snapshots: `experiments/scratch/core-seven-scan-20261003/`.

The scan used deterministic enumeration and GLOP defaults, with no random seed
or time cutoff. The exact candidate search is separate; this LP report makes
no solver-infeasibility or independently checked exclusion claim.

Reproduce the scan and pool reduction with:

```sh
uv run python scripts/scan_core_extensions.py --parents '[[1,10,22,23,25,29],[1,10,22,23,35,37],[1,5,22,23,25,29]]' --output experiments/2026-10-03/core-seven-scan --raw experiments/scratch/core-seven-scan-20261003
python3 -I scripts/reduce_core_candidates.py experiments/2026-10-03/core-seven-scan/lp-candidates.json.gz experiments/2026-10-03/core-seven-scan/dual-reduced-candidates.json.gz
```
