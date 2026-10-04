```text
Document:    Fixed Link Degree Profile Native Pilot Report
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      54d9fd1136cd144a273f10fef869098f318fdf638b1c6aebcbc048f2101c1d54
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Fixed-link degree-profile heuristic

This separate native heuristic searches for 64 distinct five-point blocks. It fixes all 19 blocks containing point 1 and changes only the 45 blocks avoiding point 1. Point 1 has degree 19, the named high point has degree 21, and all other points have degree 20. Missing triple count is the only objective. No bound or impossibility claim follows from these searches.

The four pilot seeds use link shapes 1 and 4 with high point 2, and shapes 44 and 47 with high point 3. `prepare.py` starts from three distinct full cyclic orbits on points 2 through 16, giving each outside point mutable degree 15. For high point 3 it replaces one occurrence of the link hub 2 by point 3. Each resulting seed is independently checked for distinctness, fixed-link identity, exact degrees and missing triples. Cyclic structure is used only to make seeds; moves have no rotational restriction. Labels are 1-based and saved blocks use global lexicographic order.

The three proposal types are a two-block swap directed toward a missing triple, redistribution of the symmetric difference of two blocks, and point cycles across three to six blocks. A separate legality check rejects invalid sizes, repeated slots, duplicate blocks, anchor appearances and any nonzero degree change before mutation. The fixed link is never mutable. Annealing accepts some worsening moves; periodic restarts perturb the original or best state. Every new best is saved, including improvements during restart perturbations. Move connectivity is unproved.

Preflight compiled the source with all compiler warnings treated as errors. Four two-second AddressSanitizer and UndefinedBehaviorSanitizer runs produced no diagnostics. Their 153 saved states passed independent degree/link recounts and both covering checkers, with 18 forced or sampled operation descriptors checked against before/after states. All three move types have forced apply, inverse rollback and duplicate-rejection controls. Rollback restores block slots, counts and selection flags; the missing-triple vector may be reordered. Fifteen damaged seed/profile/argument controls were rejected before an initial state was written. `seed-audit.json` checks all four input seeds using both covering checkers.

The independent source review passed before launch. Four 300-second pilots completed normally, at most two native processes concurrently, each single-threaded. No cover was found. The results are:

| Link shape | Degree-21 point | Seed holes | Best holes | Proposals |
|---|---:|---:|---:|---:|
| 1 | 2 | 60 | 17 | 260,763,518 |
| 4 | 2 | 45 | 17 | 258,086,804 |
| 44 | 3 | 59 | 20 | 270,658,098 |
| 47 | 3 | 58 | 18 | 271,517,546 |

All 264 pilot snapshots passed an independent exact recount of the fixed link and point degrees, and both covering checkers agreed on every missing-triple set. All 60 forced or sampled operation descriptors and rollback states passed. The later preflight readback checked 157 states, including the original 153 smoke states and four seed copies. Full stdout and stderr from both verifiers are saved under the ignored archive's `verifier-output/`; compact reports name and hash them. Total attempted pilot proposals: 1,061,025,966. These finite searches neither exclude their own profiles nor settle any other case.

`summary.json`, `results.json` and `pilot-audit.json` hold the results and exact saved-state checks. Each case's best witness and native log are retained alongside them. The independent source gate is in `../fixed-link-profile-independent/audit.json`. All-repository Ruff passed after this work; the native warning, sanitizer and input controls are the focused execution checks.

The frozen native source is `scripts/fixed_link_profile_heuristic.cpp`; `environment.json` records its full-file hash, compiler and binary hashes. Source copies, binaries, every saved state, stdout/stderr logs and damaged controls remain in the ignored archive `experiments/scratch/fixed-link-profile-v1.0.0/`. The sanitizer binary was built from the same source body just before the header-only SHA256 field was filled; its unchanged binary hash and this fact are recorded. The optimized pilot binary was built after the header hash was filled. Compact reports and selected witnesses are retained here. Header hashes cover the body after the header; manifests use full-file hashes.
