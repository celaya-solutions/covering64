```text
Document:    Matching Template Hull Mixed Integer Pilot
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      d5adee3773e0720414d41b7d4f160cbe70c84b9389b02cb7a80ce522bf89e26e
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Result and scope

The whole normalized matching four-sevenfold branch was searched with SCIP
10.0.0 and SoPlex 8.0.0 through OR-Tools 9.15.6755. The requested limit was
300 seconds, one worker and seed 2026100301. SCIP stopped at its time limit
after 304.86 solver seconds (304,999 milliseconds measured by the wrapper),
with eight nodes and zero solutions. Status is NOT_SOLVED. This is inconclusive.

The model is the independently audited 106-exclusion template hull: 55,528
variables and 4,550 rows. Its original 4,768 variables remain Boolean, including
all 4,368 lexicographic block variables. The 50,760 template weights are
continuous in [0,1]. There is no fixed first-heavy link and the objective is
constant zero. Later exclusions do not alter this frozen experiment.

# Why continuous weights preserve the integer projection

For each group the template weights are nonnegative and sum to one. Each of
the 69 heavy-block marginal coordinates is a binary original block variable.
If a marginal is zero, every positive-weight template has zero there. If it is
one, every positive-weight template has one there. Therefore every positive
weight has precisely the selected binary incidence vector. The complete
catalog contains no duplicate vectors, so exactly one weight is one. Conversely,
every cover surviving the checked exclusions supplies the corresponding
template in each group and extends to this model. No nonheavy block is removed.

The independent MIP audit recounted every row, column, domain and objective,
rebuilt all 69 coordinates for each of four groups, checked the distinct
template signatures, rejected 19 damaged controls, and checked the unsolved
SCIP import/export round trip. It made no solver calls. Its report is in the
neighboring `four-seven-template-mip-independent` folder.

`metadata.json`, `solve-metadata.json` and `result.json` are exact copies of
the run records. The artifact manifest binds the raw model, matrix, source,
parameters and full solver log in ignored scratch. Any numerical witness would
be saved and required to pass both covering verifiers; none was emitted.
