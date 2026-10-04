```
Document:    Filter-and-Fan Prototype Review Evidence
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      cc7f6ec680b7c736fb07b60e1b10c25c2a75ccc949acda6ef42b29c8aad58ea2
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Prototype review pack

The separate source search.cpp implements the source note's unrestricted repair tree. It does not modify the existing solvers. Both modes always use exactly 64 distinct blocks from all 4,368 lexicographically ordered 5-subsets; 1-based labels are used in witnesses. Point degrees, pair counts, core membership, template membership and symmetries are never imposed. Reused slots, returning blocks and freshly created holes affect ranking only; they are not forbidden. Duplicate resulting block sets are filtered within a tree level.

Each node enumerates all swaps whose incoming block covers at least one current hole. Weighted score is primary; raw deficit, soft history, newly exposed-hole coverage and seeded ties break later ties. Each parent retains six moves, a level retains twelve states, and trees have twelve levels by default. Weights stay fixed throughout each tree, increase on current holes between attempts, and decay every 64 attempts. The tree accepts only a prefix with a smaller raw deficit. Its greedy baseline accepts its best component move even when raw deficit worsens. Thus a future paired pilot compares two explicitly different acceptance policies as well as branching; it is not an isolated estimate of beam width alone.

The prototype retains a best improving prefix even when its time budget cuts off candidate enumeration. It returns the root unchanged when no improvement is found. Every saved trace contains the complete starting block IDs, fixed weights, all moves and scores, final block IDs and all 560 counts. Native trace emission replays the complete prefix, undoes each move and checks exact restoration. Independent check_traces.py re-enumerates triples and point degrees without using the native score implementation.

# Verification completed

- Warning-clean C++17 release and AddressSanitizer/UndefinedBehaviorSanitizer builds. Exact commands and compiler version are in preflight.json.
- Each build passed 960 random move checks and 960 complete-prefix/rollback controls, plus 10 damaged-move/state controls. Seventeen malformed seed/argument/output controls were rejected.
- The final independent readback checked 2,017 saved traces and 12,577 moves, including 12,577 moves that changed point degrees. All 14 damaged-trace controls were rejected.
- One 0.25-second sanitized smoke per mode used seed 2026100360. Both retained the existing deficit 3; beam reached depth 12. Graceful SIGTERM completed with a saved result and replayable trace. These are implementation checks, not research pilots or proof of improvement.
- The starting seed and both saved smoke witnesses were separately checked by the package verifier and scripts/check_cover.py. No 64-block cover was found. Targeted Ruff passed. Root owns the repository-wide checks and commit.

The final raw frozen pack is experiments/scratch/filter-fan-repair-v1.0.0-final-20261003. It includes source copies, release/sanitizer binaries, all command output, malformed controls, traces, seed checks, snapshots and replay results. The earlier exploratory/raw preflight folders remain unchanged. Large raw files remain outside Git.

Paired six-seed 30-second pilots have **not** been run. Root requested review of this frozen pack before those pilots. The method is heuristic and has no completeness or nonexistence claim.
