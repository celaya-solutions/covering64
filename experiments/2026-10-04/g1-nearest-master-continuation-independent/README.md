```
Document:    Independent Continued Fixed-g1 Master Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      3056150403cf52c455301a4b24afa24a46383454ede1b24126e3d899177a2d34
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Continued graph-1 nearest-master independent audit

The preparation gate independently reconstructed the continued master and checked the two diagnostic additions: one exact graph-1 separating plane and one registry-backed seven-block nogood. The continued initial model has 276 variables and 1,979 rows: 605 structural rows, 353 broad planes, 1,001 graph-1 planes and 20 registry nogoods. The complete fixed graph-1 basis, unchanged baseline objective and presolve-off five-second master parameters were verified before launch.

The independent solver-free postcheck rebuilds every one of the 42 master models in order, including every accumulated cut and nogood. It verifies each assignment, all row values, objective distance and bound, seed, parameters, solver status, registry transport and rejected-link proof reference. The status history contains 41 OPTIMAL and one FEASIBLE master result, with no UNKNOWN result. All 42 proposed heavy tuples are distinct and replace six baseline heavy blocks.

Sixteen proposals were rejected by the first-link registry and generated 18 new seven-block nogoods. The remaining 26 proposals reached the completion LP, all with numerical OPTIMAL status. The checker independently rebuilds every shifted row and recounts all 1,200-variable primal residuals. It replays all 1,001 initial and 26 newly derived graph-1 planes using integer signed weights and exact rational gaps, verifies their source tuples and numerical-dual hashes, and reconstructs all 38 final registry nogoods.

The recorded combined solver time is 115.15139658120461 seconds and wall time is 130.76688487501815 seconds, within the 120/160 caps. The checked pre-master and pre-LP cumulative guards are 113.8 and 118.9 seconds. The run stopped at the combined budget guard. The best recorded elastic objective remains 7.52051548546158. No numerical zero, exact fractional completion, covering witness, or new global bound was claimed.

All raw hashes, the complete step trace, the final nogood list and the empty improvement/stitch list were matched. All 27 files in the compressed learned-proof archive match their raw bytes exactly. Seven damaged controls were rejected: master cardinality, objective offset, heavy-plane coefficient, duplicate signed row, wrong graph family, invalid registry transport and changed presolve setting.

The initial audit run passed before a formatting-only import correction. Its source and receipt are retained in `preformat/`; abstract syntax equality was checked. The final formatted checker replays the same audit to bind the final source hash. The postcheck invokes no optimizer. Its exact exclusions apply only to their graph-1 source patterns; numerical master and LP statuses do not establish a global lower bound or exhaustive absence of other candidates.
