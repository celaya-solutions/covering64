```text
Document:    Independent Matching Template Mixed Integer Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      e93563b5d38b54c1d535fcd2e10d95ac8999e23ea257f1d714c85eb30052372e
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent matching template MIP audit

The frozen mixed-integer model passed. The independent checker reads the MPModelProto directly without importing the builder. All 55,528 variables and 4,550 rows match the separately audited matching-branch matrix exactly. Variables 0 through 4,767 are Boolean; the remaining 50,760 template weights are continuous in [0,1]. The objective is constant zero. No row, bound, or additional condition was introduced. All 4,368 candidate block indices agree with independently enumerated lexicographic five-subsets of labels 1 through 16.

For each of the four transported anchor groups, the checker reconstructs the simplex and all 69 binary heavy-block marginal coordinates. Each group has 12,690 distinct template signatures. A convex combination of binary vectors can equal a binary vector only if every positively weighted vector agrees with every coordinate: if a coordinate is zero, nonnegativity forces every active coordinate to zero; if it is one, the simplex forces every active coordinate to one. Since the signatures are distinct, exactly one template has weight one. Thus continuous template weights do not enlarge the projected integer feasible set of this already audited branch.

All 19 damaged model controls were rejected. They cover missing variables/rows, changed names, each class of integrality, bounds/nonfinite values, objectives, row coefficients/indices/bounds, lazy rows and duplicate row entries. A fresh SCIP 10.0.0 instance loaded and re-exported the model identically and accepted `SetNumThreads(1)`. This audit never called `Solve`.

The frozen candidate-handling source was reviewed separately. It saves selected blocks, requires exactly 64, checks them with the package verifier, and runs the standalone checker with `--expected-blocks 64`. It accepts only when both succeed. No MIP candidate was available during this pre-solve audit.

This is an exact translation audit against an earlier independently reconstructed normalized matching matrix, not a new audit of the unrestricted covering model. The base matrix contains reduced normalized rows; the earlier audit supplies their mathematical provenance. No fixed first link is added. Heuristic failure, a timeout, or solver-only INFEASIBLE does not prove nonexistence.

`audit.json` is the machine-readable launch gate. `check.py` is the independent checker. The raw model, matrix and frozen builder remain in ignored `experiments/scratch/four-seven-template-mip-v1.0.0/`. Full-file provenance hashes are in `manifest.json`; the document header hashes only this body.
