```text
Document:    Variable Cardinality Partial Start Pilot
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      42efdc6b7a873660d9a2ce55fb6da6db855191dfa4a1cd072c6f9520b1056d64
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Prepared comparison

Two authorized calls are prepared, in this fixed order:

| Seed | Live start | Start SHA256 | Native budget |
|---|---|---|---:|
| 2026104801 | 64 blocks, 9 uncovered triples | 15db6bdbf8c6210c6754cbe52a1408dda6a279429bb5471cf03a1b68b24f0c46 | 300 seconds |
| 2026104802 | 64 blocks, 12 uncovered triples | 330788e4a6f24e1852b047f5cd2447bfa83da66ea8c6daba3287eb53088c4b00 | 300 seconds |

Both keep the verified Belic 65-block family as a separate known complete
incumbent. Both partial families passed the package verifier and the standalone
checker with actual cardinality 64; they are incomplete, with 9 and 12 holes.
Their separate existing certificates exclude old-core overlap greater than 55
under every relabeling. All candidate, source, certificate, and control hashes
are bound in `manifest.json`.

The root agent owns launch after a new independent gate. Runs are sequential.
The first complete family of size at most 64 stops native search immediately;
the runner double-verifies all saved records before accepting it and stops
the whole campaign. No budget transfers, restarts, or relaunches are allowed.
A 315-second process watchdog allows a 5-second termination grace. Native
search still receives exactly 300 seconds per authorized call.

# Change from the completed pilot

The search kernel and four diagnostic core rows are byte-identical to the
previous pilot. The kernel SHA256 remains
`d374d813225b03d8ac9085255f9c0548e14a31a611bdc7ec5abeb0cce2040fd3`.
The original independent gate remains bound for its full score, pscore, CC,
add/drop, novelty, tie, weight, and malformed-operation controls. The new gate
focuses on changed initialization, output, and runner handling.

The driver now accepts the complete-incumbent and live-partial inputs separately.
It saves complete65, raw64, and admissible64 initial records with zero mutations.
Live cardinality counters begin at 64, excluding the separately stored complete
incumbent. After each real mutation, it considers all records and checks for a
complete cover before any further mutation. Best complete, raw exact64,
four-cap-admissible exact64, and actual final state remain separate.

Initialization reconstructs coverage counts from each new partial family.
It resets all triple weights to one, sets all configuration flags true,
sets last-flip timestamps to zero, and starts the step clock at zero. Score
and pscore are recomputed exactly from those counts and unit weights. No old
weights, timestamps, cached scores, or configuration flags are imported from
the search that produced the partial family.

Consequently, at incomplete steps 0, 1, 2, and 3, every block has age less than
four. The unchanged source policy falls back to the first lexicographic carrier
of the sampled uncovered triple. Both fixed eight-step controls exhibited
exactly four such fallback selections. This explicit initialization effect is
preserved; the experiment does not secretly advance the tabu clock.

The initial partial is guidance only. No core cap, incidence profile, protected
block, target-core restriction, or additional repair constraint enters the walk.
All 4,368 blocks retain lexicographic IDs, points remain 1-based, and all 560
triples remain present. Ranking, novelty probability, random generator, moves,
weights, no-decay policy, and stop rule are unchanged.

# Focused controls

Preparation builds the production driver and separate AddressSanitizer plus
UndefinedBehaviorSanitizer wrappers that include that same driver with a
compile-time step limit. Production compilation has no control-step macro.
A zero-step wrapper checks the real initial records and final files without
performing a search move. An eight-step wrapper checks the real initialization,
trace, record, final-state and stop paths over a fixed small replay.

For both H9 and H12, zero-step controls preserve the original family hash,
zero mutations, maximum weight one, and live min/max size 64. Eight-step controls
perform 14 mutations, reach minimum size 62 and maximum size 64, and record four
fallbacks. All 28 saved control records/final files pass both verifiers with
their actual counts. Supplying the partial family as the complete incumbent or
the complete family as the partial start is rejected before any output records.
These fixed controls do not launch either timed optimization call.

Scoped ruff and diff checks pass. The source freeze has manifest SHA256
`d66e4f2dfe7604b06dcd9d94ac49efc0c82b748b03977195e4a3924f6b2daaa5`
and control receipt SHA256
`c3913dab77915db4ab22cb33f93dc18a8eaa4b89a9e7c4b758f3905987d7521a`.
No timed optimization was launched during preparation.

After the independent gate, root may invoke:

```sh
uv run python experiments/2026-10-04/native-variable-partial-start/run.py \
  --gate experiments/2026-10-04/native-variable-partial-start-independent/gate.json
```

Any eventual failed run remains inconclusive for the global covering number.
