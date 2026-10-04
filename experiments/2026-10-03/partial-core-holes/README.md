```text
Document:    Joint Core Escape Partial Cover Pilot
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      db01bdb175eefa48913616be58ea8b4643981a7f4855dfa72f83c5e935a83754
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Result

One 180-second, one-worker CP-SAT pilot found no improvement over its
11-hole starting hint. The result was FEASIBLE, with a zero objective lower
bound. The only saved state retains 55 blocks of the specified original core.
Both covering checkers agree it is incomplete. No cover, useful escape seed,
global bound, or infeasibility result was found.

The separate integer-only structure screen exhausted its mapping search and
found no relabeled copy of the 60-block core in that state. It nevertheless
contains five disjoint heavy triples with multiplicities 6, 7, 6, 6, 7. This is
the already proved forbidden five-heavy-triple profile, so the state was rejected
as a useful escape seed. A structure screen is not a coverage test; any full
64-block cover must pass both covering verifiers regardless of its profile.

# Model and initialization

The model has all 4,368 five-block variables in lexicographic order, exactly
64 selected blocks, and 560 exact missing-triple indicators. It minimizes their
sum. Original-core overlap is constrained to 52 through 55. This is a chosen
construction band, not a complete restriction on possible covers. There are no
degree, regularity, rotational, or maximum-hole constraints.

The checked input has three holes and contains all 60 core blocks. Initialization
removes the five core blocks with smallest original private-triple loss, breaking
ties lexicographically. It then greedily adds five distinct non-core blocks by
new triple coverage, also with lexicographic ties. The resulting feasible hint
has 11 holes and core overlap 55. During optimization every block variable is
free; the initial deletion choice is not a frozen neighborhood.

The exact missing indicators use both directions: an indicator is true precisely
when no selected block covers its triple. The independent model gate rebuilt
all 4,928 variables and 1,122 rows directly and verified the complete hint.
Seven damaged model controls were rejected. The source and exported model were
frozen before the authorized pilot.

# Difference from earlier work

The five-core-deletion requirement was already used in zero-hole exact models:
both complete degree branches included checked original and relabeled core cuts
and returned UNKNOWN after 600 seconds each. Native single-exchange escape
campaigns also required 15 or 18 absent original core blocks, yet returned
three-hole states with original-core overlaps 33 and 1. A labeled overlap alone
therefore does not establish a different structural basin.

The earlier 600-second partial-cover core LNS fixed randomly chosen retained
blocks before each repair. It allowed at most six holes, never requested a core
cap below 56, and achieved overlap no smaller than 58. Filter-fan runs had no
core-overlap condition. This pilot instead jointly selects core deletions and
replacement blocks in a positive-deficit optimization with no six-hole ceiling.
Its bounded failure does not exclude that strategy or the chosen band.

# Evidence and reproduction

Seed: 2026103991. OR-Tools: 9.15.6755. Solver time: 180.001662 seconds.
Source revision: deeaaca413d5032eb5ec37d1ef8499fae4af93cc.

- `metadata.json`, `input-audit.json`, `hint-audit.json`, and
  `initialization.json` record the frozen inputs and deterministic construction.
- `check_independent.py` and `gate.json` are the independent root-agent model gate.
- `result.json` and `solution-000-h11.*` record the only solver candidate.
- `screen_structure.py`, `structure-audit.json`, and `hint-structure.json`
  record the separate label-invariant profile and relabeled-core checks.
- `check_structure_controls.py` and `structure-controls.json` validate six
  positive containment controls, one negative control, and six damaged inputs.
- `manifest.json` hashes compact evidence and ignored raw evidence. Raw source,
  model, solver log, stdout, stderr, and launch receipt remain under
  `experiments/scratch/partial-core-holes-v1.0.0/`.

The structure detector is complete when it reports `search_complete: true`:
any core embedding maps its five disjoint sixfold triples to five disjoint
candidate triples of multiplicity at least six. The detector tries every such
group assignment and every within-group point permutation. Degree, pair, and
triple pruning uses only necessary containment inequalities. Every found map
is checked against all 60 blocks. A timeout reports unknown and cannot qualify
a useful seed.

Recheck the structure evidence without running a solver:

```sh
python3 -I experiments/2026-10-03/partial-core-holes/check_structure_controls.py
python3 -I experiments/2026-10-03/partial-core-holes/screen_structure.py \
  experiments/2026-10-03/partial-core-holes/solution-000-h11.txt \
  experiments/2026-10-03/partial-core-holes/core.txt \
  --output experiments/scratch/partial-core-holes-recheck.json
```

The frozen runner records the supplied gate receipt's hash but does not itself
validate the receipt's pass flag or model hash. This pilot was launched only
after the root agent independently checked the actual matching gate. A future
runner version should enforce those fields; do not alter this frozen version.
