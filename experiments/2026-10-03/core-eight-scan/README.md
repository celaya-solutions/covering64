```
Document:    Bounded eight-removal core extension audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      d3b5d7b7c9848b8f2bf10d9122f8798c23856f093418a69f0157dbc7518224fa
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Bounded eight-removal extension scan

This batch covers155 subgroup classes of one-block extensions of exactly these seven-removal parents:

- 1,3,10,22,23,25,29
- 1,10,20,22,26,29,37
- 1,3,10,22,26,29,37

The core is the fixed60-block Belic core with SHA256 `7011e57be2714b1e1a16d4419ecb55a0160e25806f5db5dd786891aa17d0a5db`. Each neighborhood retains52 blocks and allows12 additions. The batch does not enumerate all eight-removal neighborhoods.

`scan.json.gz` retains exact feasible dual weights and source metadata. `check_scan.py` independently reconstructs the60-element subgroup, enumerates the specified extension family, checks every case appears exactly once and checks every rational capacity over all4368 blocks. All155 cases pass. The LP stage alone excludes none.

`dual-reduced-candidates.json.gz` reconstructs exact duals with11 < B <=12. In any12-block completion, every selected block must have dual load at least B-11, since each other block has load at most1. Rechecking all4368 possible blocks therefore retains every possible completion. `check_pools.py` independently verifies the weights, uncovered support, cutoff and entire allowed pool in all155 cases. Pool sizes range77–198; the smallest reconstructed bound is2447/208. Its removal set is1,3,10,22,23,25,29,43.

Both independent audit outputs are included. The reduced artifact SHA256 is `d8ac83a6b9a08c6c80752b700f1185fbb9e053777484df858dc42b2a694623d3`. These audits certify the stated scan and safe reduction, not infeasibility. A separate CP-SAT run reported all155 reduced kernels INFEASIBLE; solver status alone is not an independently checked theorem. Any separately replayed proof must be cited separately.

Generation started2026-10-03T19:17:51Z at revision `d57346da01d6f8afbd65dee0981dddc97ceea27d`, Python3.13.15, OR-Tools9.15.6755. Source hashes and the2.456873-second generation time are in the scan metadata. Raw snapshots and logs are in `experiments/scratch/core-eight-scan-20261003/`; CP outputs are in `experiments/scratch/lns-r8-dual-kernels-20261003/`. No nine-removal extension was started.

Run the independent checks from the worktree root:

```sh
python3 experiments/2026-10-03/core-eight-scan/check_scan.py experiments/2026-10-03/core-eight-scan/scan.json.gz
python3 experiments/2026-10-03/core-eight-scan/check_pools.py
```
