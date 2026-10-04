```text
Document:    A Native Hole-Minimizing Search in the Two SQS Extension Pool
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      27c8225e7088aec9e550094a90756d2d05e0a84a2b8a79492a2f06373bfa1868
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Prepared constructive search

This heuristic searches for exactly 64 distinct five-blocks drawn from the
fixed 1,744-block union of the affine and traded SQS(16) extension pools.
Only membership, distinctness and cardinality restrict the family. There are
no point-degree, fixed-core, orbit or symmetry constraints. Point labels are
1-based, and all 4,368 global five-block IDs follow lexicographic order.

The deterministic start repeatedly selects the allowed block covering the most
currently uncovered triples, breaking ties by smallest global ID, until it has
64 blocks. `prepare.py` records the 64-step trace and start, all **107,520** legal
one-out/one-in initial replacement deltas, and 96 deterministic move controls.
The controls exercise acceptance, rejection, and positive-delta tentative moves
followed by complete rollback. They expose all 560 cached counts and 64 selected
IDs after each action, including checkpoints after every four accepted moves.
These finite checks do not run optimization.

The separate `scripts/sqs_pool_heuristic.cpp` has three modes:

- `prepare POOL OUT`: generate the finite start and audit artifacts.
- `validate POOL START`: check strict input structure and full-state counts.
- `run POOL START SEED SECONDS OUT`: run the annealing search.

Pool input must contain exactly 1,744 increasing global blocks. Start input
must contain exactly 64 distinct members of that pool. Both require strictly
increasing point labels in 1..16 and exactly five integer labels per block.
Duplicate blocks, malformed labels, unordered data and out-of-pool starts are
rejected. The manifest and gated runner bind the permitted pool's exact hash;
the native parser alone does not identify a particular named pool.

## Search and recounts

Each proposal replaces one selected block with one unselected allowed block.
Half the proposals sample the entire pool; half sample a block containing a
random uncovered triple. Thus every allowed replacement remains available.
The unweighted energy is the number of uncovered triples. Non-increasing moves
are accepted; increasing moves use the explicit annealing probability in the
source. Temperature follows `0.05 + 0.75*(1-phase)^3`, with phase advancing over
250,000 proposals before reheating. This proposal rule is heuristic and does
not assert equilibrium sampling or completeness of a finite search.

Every accepted move checks its predicted delta against the updated counts.
After every 4,096 accepted moves, every new best state, and at the end, the
program rebuilds all 560 counts by direct triple containment. It verifies 64
distinct pool members, every cached count, and the uncovered count. Every best
partial family is saved, even if it is not a cover.

## Gate and pilot result

The separate independent gate passed all 107,520 initial replacement deltas,
96 move controls and eight accepted-count checkpoints. Both covering verifiers
agreed on 65 distinct actual or tentative audit states. An address/undefined
behavior sanitizer build reproduced all five preparation files; 20 malformed
inputs were rejected by both binaries, and nine damaged traces were rejected.
The gate is in `../sqs-pool-heuristic-independent/gate.json`.

After root review, the single authorized pilot used one process, seed
**2026104021**, for **60 seconds**. It completed in **60.0003 seconds** and
improved the greedy start from **31 holes to 23 holes**. No cover was found.
It made 277,385,022 proposals, accepted 5,245,095 moves, and completed 1,290 full
recounts. The final annealing state had 34 holes; the best saved state retained
23 holes. No repeat run was made.

All nine saved best states (31 through 23 holes) and the final state passed
pool-membership, cardinality and distinctness checks. Both covering verifiers
agreed on their exact missing triples and correctly rejected each as a cover.
`check_pilot.py` passed and rejected all 11 damaged-result controls.
`pilot-result.json` has SHA256
`a94c44185a4a01a553d5a9293f2da1238a3b670af13e95d3419aa3683dba250a`.
The best partial family's SHA256 is
`82b23d83e92f4c61c3c9fc6704b9cc1204122f4a928a48ab9d24712916ff7224`.
The full run is saved under the scratch folder's `pilot-2026104021/` directory.

The frozen manifest records source revision,
source and binary hashes, compiler/version/flags, the original pool and text
pool hashes, greedy start hash, preparation artifacts and malformed controls.
Raw evidence is in `experiments/scratch/sqs-pool-heuristic-20261003/`.

`run_pilot.py` verifies the manifest, all frozen artifacts and independent gate
before invoking the native process once. It refuses to overwrite the run
directory. It sends every saved best family and final family through both
the package verifier and standalone `scripts/check_cover.py`, comparing their
exact uncovered triples and canonical hashes. `check_pilot.py` reads back the
run, checks accepted-count recount checkpoints, repeats both verifiers, and
rejects damaged result controls.

A positive hole count is a partial family, not a covering witness. A finite
failure to reach zero is inconclusive and cannot establish an unrestricted
lower bound or exhaust this pool. Any zero-hole family must pass both covering
verifiers before being called a cover.
