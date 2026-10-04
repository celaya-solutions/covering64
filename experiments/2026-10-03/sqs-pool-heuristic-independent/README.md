```text
Document:    Independent Gate for the SQS Pool Native Heuristic
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      998d1ffd2b0bd85405580d00d0170f28190d34a19fbaeb0b92fed00e7715d054
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Gate result

The frozen pool-only native heuristic passed this finite implementation gate.
No timed optimization was run by this audit. The gate does not claim a cover,
extendability, or a global lower bound.

The independently reconstructed pool contains 1,744 blocks. Its deterministic
64-step greedy start has 31 missing triples. All 107,520 legal initial
replacements were checked: 49 preserve the hole count and the rest increase it.
This is a statement only about that initial one-replacement neighborhood.

# Independent reconstruction and state checks

`reconstruct.py` rebuilds both SQS seeds from affine triple completion and the
four-pair transversal trade, then scans all 4,368 five-subsets for membership in
the union extension pool. Greedy choices maximize newly covered triples, with
ties resolved by global lexicographic block ID. All 64 choices, gains and hole
counts match the native trace.

For each initial replacement, the checker rebuilds the covered-triple union of
the 63 retained blocks and then adds the incoming block. This independently
checks the complete delta table without reusing the native incremental-delta
formula. All removed IDs, incoming IDs, slots, deltas and resulting hole counts
match, with no missing or repeated pair.

The 96 scripted proposals comprise 32 accepted moves, 32 rejections and 32
positive-hole-delta tentative moves followed by rollback. The audit directly
recounts every actual and tentative state and checks the entire selected-ID
vector, all 560 cached counts, hole score, accepted counter and eight periodic
checkpoints. Rejected and rolled-back states exactly match their prior states.
Both covering verifiers agree on all 65 distinct actual or tentative states.

# Native source and sanitizer controls

Source review checks every entry path: greedy selection iterates only the
allowed pool; loaded starts require membership; proposals use either that pool
or triple carriers built only from it; `State` construction, replacement
validation and full recounts enforce membership and distinctness. No degree,
regularity, fixed-core, orbit or symmetry restrictions are imposed. Runtime
full recounts occur every 4,096 accepted moves, on improvements and at exit.

The native engine operates on a supplied 1,744-block pool. The authorized runner
pins that input to the independently checked SQS pool through its frozen hash
and validates every manifest and gate input before launch.

A fresh build with AddressSanitizer and UndefinedBehaviorSanitizer reproduces
all five optimized preparation artifacts byte for byte, with empty stderr.
Twenty malformed, duplicate, unordered or out-of-pool input cases are rejected
by both binaries. Nine damaged move traces are rejected by the independent
replayer. All relevant Python files pass Ruff.

# Frozen evidence

- `check.py` and `gate.json`: full gate, source/input hashes, all delta and
  move checks, sanitizer results and both-verifier state receipts.
- `reconstruct.py`, `expected.json`, `expected-greedy.txt`: independently
  reconstructed reference start, greedy trace and complete-delta digest.
- `expected-greedy.package.json` and `expected-greedy.standalone.json`:
  direct agreement on the 31-hole reference state.
- `manifest.json`: compact and ignored raw evidence hashes.

Large delta traces, binaries, compiler records, malformed controls and the 65
state/verifier triples stay under ignored
`experiments/scratch/sqs-pool-heuristic-independent-20261004/`.

Frozen native source SHA256:
`bb8b202dea60e8f32bc882fe93ae0ec76c7f8f5d676785c2fd547f7998ac3cf6`.

Frozen preparation manifest SHA256:
`f63904259b1377960533116ddcd296923f9beeec9b5277ef4512c2ac297e1b8f`.

Recheck finite controls without timed optimization:

```sh
uv run python experiments/2026-10-03/sqs-pool-heuristic-independent/check.py
```
