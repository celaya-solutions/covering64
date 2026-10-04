```text
Document:    H9 D23 Strict-First Neutral Queue Pilot
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      2a8ba8c4cd11fd2b6c49e065981a1de4cd7be597613fb6b93c3db7adaa840c1d
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Audited native start

This pilot begins with the best weak-qualified family from the completed,
independently audited two-seed five-core native pilot. The family has 64
distinct blocks, nine holes, D2max 23, D2sum 29, minimum pair count five, and
zero D3 and D4. Its hash is
`f5f24d57738763380c715769eef4328d7f1950a8ae6d0eedd8e9ff16dc3fc681`.
The second seed's ten-hole family has lower D2max but loses the hole-first
ranking. The raw native H9 family is a different, unqualified family.

Preparation pins the completed native manifest, result, runtime audit, source
files, saved families, and raw files. It chooses the minimum audited qualified
rank `(holes,D2max)`, with the full lexicographic block-ID tuple as tie break.
Both unchanged recorder paths and both cover verifiers check the initial
family. It is a partial cover, so both full-coverage verdicts are false.

# Unchanged shell search and bounded queue

The pilot reuses the frozen one-swap and two-swap binaries, original adapter,
evaluation headers, weak rules, four named cap55 filters, and bounded wrapper.
There is no native recompilation or change to any shell kernel. The frontier
starts with this one H9 family. All 34 previous visited hashes remain excluded;
there is no seed-revisit exception.

The allowance is at most 16 centers and 32 sequential shell calls. Each call
keeps its 120-second kernel budget, 135-second watchdog, and five-second grace.
Each center runs one-swap then two-swap. Both completed shells contribute
strict candidates; the lowest rank and full-ID tie break select the next
center. Strict descent clears worse-rank pending states. Otherwise the queue
adds unseen retained neutral states and chooses the full-ID minimum.
Results preserve every pending state, including a popped next center.

Preparation recomputes the one-swap distance to every historical family from
its pinned witness. It requires every distance to exceed 32. At most 15
two-swap center transitions precede center 16, and any candidate inspected
there is at distance at most 32 from the start. Thus no historical hash can
be reached within this budget, and the unchanged strict-visited guard cannot
trigger because of a historical join. This argument does not apply to a
longer campaign without a new bound.

The fifth named common62 cap56 is reported only, and does not change the shell
filters or acceptance rules. Its start overlap is one. Each two-swap move can
add at most two core blocks, so any inspected candidate has overlap at most
33 within this budget. That is below the fixed named cap56. This is a
budget-dependent observation, not an unrestricted reduction or a claim about
every relabeling of the core.

The runner stops at a cover, incomplete shell, empty retained sample frontier,
or the center budget. A shell retains only its first 64 neutral families in
traversal order before sorting them. These are not necessarily the globally
smallest 64, and exhausting retained samples does not exhaust a plateau.
Only completed shells support a local strict-closure claim. Any candidate
still requires both cover verifiers; this pilot cannot prove a global bound.

Eighteen synthetic controls cover queue order, strict preference, retained
frontier preservation, historical exclusion, incomplete and cover stops, the
16-center/32-shell cap, and malformed frontiers. Preparation launches no
search. Root alone may launch the frozen runner once after independent GO,
using `run.py --gate PATH --gate-sha256 SHA --execute`. Relaunches and budget
transfers are forbidden; existing results or the output folder stop a launch.
