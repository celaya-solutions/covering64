```
Document:    One Unrestricted Repair of the Five-Hole Seed
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      762222782816af3f63b2b3daee97b2a2999284c2ae01c72ec5a56d51953c9fa2
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Result

The single authorized repair improved the LP-guided 64-block near-cover from
five holes to three holes. It found no cover. Both the package and standalone
checkers agree on all four saved states: initial, accepted improvement, best,
and actual terminal state. The best and terminal states are identical.

The remaining missing triples are (4,8,12), (4,8,16), and (8,12,16). The best
canonical SHA256 is
`5389846a1e0434406c377fa44751ccac96d78334c0286bb64a7beca46f395492`.

# Bound and replay

The existing frozen filter-and-fan binary ran once with seed 2026104061, one
worker, and a 60-second budget in beam mode: width 12, fan 6, depth 12. All
4,368 five-element blocks were available and all 64 slots were mutable. No
degree, pair, heavy, anchor, or other structural constraint was imposed.

It finished normally after 60.0001 native seconds and 60.316876 wrapper seconds,
with 1,865 trees and 3,181,199,872 proposals. Stderr was empty. The frozen
independent trace checker replayed all 1,865 saved traces and component moves,
including exact counts, legality and rollback, and rejected its 14 damaged
controls. Each saved trace contained one recorded move; the depth cap does not
mean that every internal explored path was serialized.

There was one accepted improvement: global lexicographic block ID 3081,
(4,5,6,7,8), was replaced by ID 3084, (4,5,6,7,11). IDs here are zero-based
column positions; point labels remain one-based. This removes one original
heavy pin. The proof excluding completion of the original 28 pinned blocks
therefore does not apply to this new state.

`audit_states.py` checks every trace root against the actual current slot
order, updating current only for accepted `improvement` records. Exploratory
endpoints are not treated as terminal current. It saves each accepted state,
checks the final current against the native best file, and runs both cover
verifiers on each saved block file. Trace count equals the native tree count.
`terminal.txt` records the true final current, not an unaccepted beam endpoint.

# Structural comparison

The old unrestricted three-hole seed had point-degree histogram 19:3, 20:10,
21:3. This new state has histogram 19:1, 20:14, 21:1. Its triple multiplicities
are zero:3, one:498, two:54, six:1, seven:4. These invariants differ from the old
seed, so it is not merely a relabeling of that complete 64-block family.

However, the established structural detector found a relabeled 60-block Belic
core in 18 group nodes. The returned point map was independently checked
against every core block by `audit_states.py`. The five disjoint heavy triples
are (1,2,3), (5,6,7), (9,10,11), and (13,14,15), each sevenfold, together with
(4,12,16), which is sixfold. This is the already excluded five-heavy profile,
and the state is not an escape from the old structural basin. Original-label
core overlap is zero, illustrating why the relabeling check is necessary.

# Evidence

`manifest.json` binds the frozen source, binary, seed, gates, versions and
launch command. `result.json` preserves the one run's termination and summary.
`trace-audit.json`, `state-audit.json`, both verifier outputs per saved state,
and `core-structure.json` preserve the independent checks. `files.json` binds
all compact evidence. Full raw traces, logs and frozen input snapshots remain
outside Git in `experiments/scratch/five-hole-unrestricted-repair-2026104061`.

This was one bounded construction attempt. It does not prove nonexistence
and it does not improve the earlier three-hole record. The best verified full
cover remains 65 blocks. No repeat or additional search was launched here.
