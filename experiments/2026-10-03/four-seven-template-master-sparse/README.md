```
Document:    Sparse Heavy Pattern Seed Master Pilot
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      17eac9e5922b4d60a48fc561ff3be7254b6fe4ce0f6d34d6cb84465a664ca4af
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Purpose and scope

This is a seed generator for the normalized matching four-sevenfold branch. It keeps 276 allowed heavy-block variables Boolean and relaxes ordinary-block and double variables to continuous values. The sparse master keeps only the 4,768 original variables and 4,270 original rows. It removes the template-hull extension, so any proposed heavy pattern needs a separate 108-catalog eligibility check.

A feasible master would supply four heavy patterns, not a 64-block cover. A separate integer completion and both covering verifiers would still be required. No unrestricted assumption or theorem follows from these experiments.

# Independent model gate

The separate sibling audit reconstructs the allowed heavy columns and verifies all preserved protobuf fields. The full relaxation changes exactly 4,492 integrality flags; the sparse relaxation then removes exactly 50,760 variables and 280 rows. Both gates reject eight damaged controls and check an unsolved SCIP import/export round trip.

# Bounded result

SCIP 10.0.0 / SoPlex 8.0.0, one worker, seed 2026103902, requested 30 seconds. The result was **NOT_SOLVED**, after 30.049 solver wall seconds and 27 nodes, with zero solutions and no pattern seed. This timeout is inconclusive.

Settings, result and hashes are preserved beside this report; the frozen model, source snapshot and solver log remain under the ignored raw directory named in `evidence.json`.
