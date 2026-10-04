```text
Document:    A Certified Symmetry Pilot for the Two SQS Extension Pool
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      f36830cff758fe4c52133d99ff064744ab45157c6748fd4122338f80cade26a2
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Prepared model

This experiment preserves the complete base model for exactly 64 five-blocks
from the fixed 1,744-block union of the affine and traded SQS(16) extension
pools. It appends exactly one linear constraint: at least one of the six
certified representative blocks is selected. The model has 1,744 Boolean
variables and 562 rows: one exact64 row, 560 triple-coverage rows, and the new
representative row. Variable order and every field of the base protobuf remain
unchanged. No objective, hint, fixed block, incidence profile or invariant-cover
assumption is added.

The appended row has local variable IDs `[132, 543, 1688, 1691, 1692, 1694]`,
coefficients `[1, 1, 1, 1, 1, 1]`, and domain `[1, 6]`. The corresponding global
lexicographic block IDs are `[308, 1295, 4312, 4315, 4316, 4318]`. All point labels
remain 1-based.

## Completeness of the representative restriction

The independently checked certificate in `../sqs-union-symmetry/` gives 1,536
point permutations preserving both seeds and their extension union. The
stabilizer of the triple `{9,10,11}` has 48 elements. Its action partitions the
30 pool blocks containing that triple into six orbits of sizes
`[12,8,3,1,3,3]`, with the six listed representatives. Each carrier has a stored
stabilizer element mapping it to its representative. The certificate audit
explicitly checked all group maps and rejected 14 damaged-certificate controls.

Any cover selects a block containing `{9,10,11}`. Apply the certified pool
automorphism mapping that selected block to its orbit representative to every
block in the cover. The result remains a cover in the same pool, keeps its 64
distinct blocks, and satisfies the new row. Conversely, any solution with the
new row also satisfies the unmodified base model. Thus the two models are
equivalent for existence under pool-preserving relabeling. The added row is
**not** a necessary inequality for every labeled cover.

## Gate and bounded pilot

`build_model.py` binds the base model, pool, certificate, certificate audit and
their source hashes before exporting. Its manifest records those hashes,
the exact added row, source revision and OR-Tools version. The builder confirms
that deleting only the last constraint restores the original protobuf's exact
deterministic serialization.

The independent `check.py` gate passed: deleting the last row restores the base
protobuf exactly, the appended row contains only the six specified variables,
and all 30 stored carrier relabelings are bijections preserving the entire pool
and mapping the carrier to its representative. Seven damaged models or
certificates were rejected. The gate and checker are frozen in this folder.

After root review, the authorized single pilot used seed **2026104011**,
**180 seconds**, **one worker**, and OR-Tools **9.15.6755**. It ran from
2026-10-04 05:41:36.135744 UTC to 05:44:36.163767 UTC and returned **UNKNOWN**
after **180.003770 seconds**, with 3,184,916 conflicts and 318,468,715 branches.
No witness was produced, and no repeat search was run. This is inconclusive.

`run_pilot.py` checked all frozen inputs and refused to overwrite the single
run directory. `check_pilot.py` verified the recorded parameters, solver
response and artifact hashes and rejected all **12 damaged-result controls**.
The readback is in `pilot-readback.json`; the result is in `pilot-result.json`,
with SHA256
`eda39782831889843e95396250d75085b4130ca85a5e67ec917ea40f0ac47b4a`.
Raw run artifacts are under the scratch folder's `pilot-2026104011/` directory.

Any candidate must pass both the package verifier and standalone
`scripts/check_cover.py`. UNKNOWN or timeout is inconclusive. Solver INFEASIBLE
would concern this fixed extension pool and would not itself be an independently
checked theorem. This experiment cannot give an unrestricted lower bound on
C(16,5,3), and no 64-block cover is claimed.

The earlier unmodified-pool pilot returned UNKNOWN in 179.996219 seconds with
seed 2026104001. This is a new model using a proved representative restriction;
that earlier pilot and all of its artifacts remain frozen.

The exported model and large run artifacts are outside Git in
`experiments/scratch/sqs-union-symmetry-pilot-20261003/`.
