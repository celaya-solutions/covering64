```text
Document:    Anchor-Pair Lookahead Native Cycle Pilot Results
Version:     v1.2.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      10365cc0f8f4a0431d7750e1905fc91251458d0b70281c1aed295e8b5fcd71fb
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Result

The one authorized cycle pilot completed normally after 300 search seconds with
one native worker. It improved the verified 12-hole starting state to 10 holes.
No covering was found; this does not exclude any covering family or establish
a global lower bound.

| State | Holes | Base soft score | Unsupported triples | Total score | Admissible ordinary blocks |
|---|---:|---:|---:|---:|---:|
| Starting v1.1 cycle state | 12 | 92 | 1 | 192 | 542 |
| Raw and score best | 10 | 78 | 0 | 78 | 680 |

Both best records are the same state, SHA256
`8bfb962deaeeede2032d9efac1783f7eaabde38aada16c8f5fecdd2f19f84ef3`.
Its pair-target L1 is 8 and its nonheavy excess is 4. It is byte-identical to the
separately verified performance-smoke state. The longer run retained that best.
The native process attempted 72,308,652 main-loop proposals and 144 restarts.
It made 17,041,214 cache misses, 1,095,441 hits and 170 production cache clears.
Full per-mode counters and pair/triple diagnostics are in `summary.json`.

# Independent gate and verification

The pre-pilot gate in `../four-seven-template-lookahead-independent/` compared
32 fresh heavy tuples against a Python oracle that recomputes full H+B counts.
It compared complete admissible-block and unsupported-triple sets, including
nonzero-heavy-excess and zero-unsupported cases. A fresh ASAN/UBSAN build was
clean. It checked 38 fresh states and eight operations covering all four move
classes, ordinary-move cache invariance, template rollback, two cache
clear/refill/reset controls, and 14 damaged score fields. Only afterward did
the single 300-second pilot start, from the original 12-hole seed.

Primary final-source preflight separately checked 30 optimized-smoke snapshots
and four forced moves, plus 44 sanitizer snapshots and eight forced moves.
Every saved state passed both covering checkers and the complete lookahead-set
recount. Seventeen damaged inputs were rejected. The three-second optimized
smoke exercised a real production-capacity cache clear and found the ten-hole
state; its witness and both checker outputs are saved here.

The completed pilot audit independently checked all 54 saved states and 16
operation records. Both covering checkers agreed on every state. Exact
lookahead sets, hole and score deltas, and forced rollbacks passed. The best
record/log audit checked both minima, aliases, saved search states and logged
scores. Native stderr was empty. Zero unsupported triples is only a necessary
condition for completing a heavy tuple; no completion is implied.

# Design and provenance

`DESIGN.md` gives the forced anchor-pair proof, excess test, high soft penalty,
cache rules and unconditional zero-hole acceptance. No hub-hub pair target was
made a hard lookahead constraint, and legal moves were unchanged. The frozen
native source SHA256 is
`e9584eb88bb4bb744b7a2d83af26d1f3f3cf23c5efeeb42a1d94438582c4da35`.
The v1.0 and v1.1 baseline sources and all completed evidence were preserved.

`environment.json` binds compiler/build settings, binaries, source revision,
helpers and seed manifest. `preflight.json` binds the independent gate and
records the preserved draft-cache-control and corrected audit-output-path
provenance. `seeds.json` includes matching only for short controls; the pilot
runner explicitly permits cycle only, 300 seconds and one worker. Full native
state sidecars, oracle/cache controls, binaries, source snapshots and verifier
output remain under ignored
`experiments/scratch/four-seven-template-native-lookahead-v1.2.0/`.
