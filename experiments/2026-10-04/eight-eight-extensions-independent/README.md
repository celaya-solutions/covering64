```text
Document:    Independent Eight by Eight Extension Model and Runner Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      ddc03ce645a5a3ef86546623937e8a46e380196316f651fb69f364cacdc4e750
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent audit

GO for the three frozen restricted recipes AA, AB and BB, with one 120-second,
four-worker call each and seeds 2026105401 through 2026105403. Root owns the
production launch. This audit launched no solver and changed no producer artifact.

The independent checker reconstructs every base using three-coordinate binary
dot products, then derives each eligible column by intersecting the full
lexicographic five-subset list with its eight-point half. It compares all group
JSON and the entire standard protobuf to the reconstruction. Each model has
4,368 lexicographic block variables, 1,472 eligible columns, 64 disjoint groups,
and 625 rows: one exact-cardinality row, 64 exact-one group rows, and 560 triple
cover rows. Each triple row retains all 78 containing columns, including those
fixed to zero. Full protobuf equality excludes hidden objectives, hints,
auxiliary variables, enforcement literals, and extra constraints. Native model
validation also passes.

All 60 deliberate model/group damages are rejected. Six fake child cases verify
the three seeds, exact time and worker settings, one solve call per child, full
final-vector persistence, and UNKNOWN versus FEASIBLE output behavior. Seventeen
fake outer-runner cases cover three-run UNKNOWN progression, watchdog termination,
forced kill, nonzero exit, absent outcome, callback persistence, invalid vector,
atomic partial-file handling, nine gate/input/prior-run rejections, and relaunch
rejection. The synthetic feasible cases are control-flow tests, not candidates.
The real solver method is guarded to fail if called by this audit.

The inherited collector retains all 4,368 values. With no auxiliary variables,
its tail is empty, so it stops at the first feasible callback. Feasibility still
requires all model cover rows; this is not a zero-hole-auxiliary interpretation.
The outer runner checks saved vectors against every serialized row and domain,
then invokes both real cover verifiers through the common helper before saving
a cover. The common dual verifier deliberately requires exactly 64 blocks.

A separate ordinary positive control uses every one of the 4,368 distinct
five-subsets. It passes the common family writer, common model reader, common
vector checker, and both actual verifiers at cardinality 4,368. Six malformed
vectors are rejected. A synthetic callback using this real ordinary family
saves all values atomically and stops once. This proves helper behavior only;
no feasible vector for any restricted 64-block model is known from this audit.
The large ordinary model is reproducible and its hash is retained, but its bytes
are deleted after the test. The witness and both verifier receipts are kept.

The separately authored conceptual receipt is hash-bound in the gate. Its
finite recount checks all 3,003 eight-quadruple subsets of the affine SQS(8).
Exactly 35 have every point in four quadruples: seven type A and 28 type B.
Thus AA/AB/BB cover that regular affine-base template up to half relabeling and
half exchange. This is not completeness for arbitrary covers, arbitrary
partitions, or nonregular quadruple choices. The model audit independently
reconstructs the three frozen representative models.

UNKNOWN, a timeout, and CP-SAT INFEASIBLE do not settle unrestricted existence.
Any found candidate requires the package and standalone verifiers. Direct
`--child` is an internal invocation path, not a security boundary; the authorized
production path is the hash-gated outer runner.

Reproduce with `uv run python
experiments/2026-10-04/eight-eight-extensions-independent/audit.py`.
Ruff passes for the audit source. Root retains responsibility for the repository
test suite, Git checkpoint, and AGENTS note.
