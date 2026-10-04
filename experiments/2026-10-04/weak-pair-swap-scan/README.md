```text
Document:    Weak Pair Complete One Swap Scan
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      da3829a45b622ae99d1ced367b5d2ec45838800780e6ef6de83562a2c5049b87
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Scope and frozen start

This is one bounded exhaustive scan of the pinned 64-block CP family whose
SHA256 is `cadb86e4f2243eada269dc314bca0bc5c238f5b0ca2bd9525dd0b67aad24c970`.
It starts at 12 uncovered triples and a sum of 32 per-pair maximum stronger-row
deficits. The expanded 10,920-row deficit sum is also 32. Its pair floor is 5,
all 1,680 single and 10,920 quadruple necessary rows pass, and four core overlaps
are `[1,1,1,2]`.

Every outgoing block is one of the original 64. Every incoming block is one of
the 4,304 originally unselected blocks in the complete 4,368-block universe.
The fixed nested lexicographic loops therefore evaluate exactly
`64 * 4304 = 275456` neighbors if uninterrupted. Point labels remain 1-based;
internal block IDs are 0-based positions in global lexicographic order.

No neighbor is repeated: its outgoing block is the unique member of the initial
family absent from the neighbor, and its incoming block is the unique member
of the neighbor absent from the initial family. Conversely every one-block
replacement has exactly that outgoing/incoming pair. There is no symmetry or
regularity reduction and no restricted incoming block pool.

# Rows, rank, and affected-pair completeness

A legal neighbor has exactly 64 distinct blocks, minimum pair count at least 5,
zero single-cut deficit, zero quadruple-cut deficit, and overlap at most 55
with each of the four frozen named cores. For each pair P the checked rows are
`13 - 3*c(P) + c(P union {a}) <= 0` for all 14 other points, and
`12 - 3*c(P) + 2*c(P union {a,b}) <= 0` for all 91 other point pairs.
No hard D2zero, global profile, point regularity, or new core restriction is added.

Legal neighbors are ranked lexicographically by:

1. Number of uncovered triples.
2. Sum over 120 pairs of each pair's maximum positive stronger-row deficit,
   computed from its two largest triple counts.

The sum over all 10,920 individual stronger-row deficits is reported separately;
it is not substituted for the second rank coordinate.

Only pair-row groups affected by a swap need updating. The affected set is the
union of all pairs contained in the outgoing or incoming block, including
intersection pairs whose pair-count delta is zero. If a triple or quadruple
count in a row indexed by P changes, that subset lies in one of the changed
blocks and contains P; therefore P lies in the union. All rows outside the union
are unchanged from the separately verified legal initial state. This argument
covers the pair-floor, single, quadruple, and stronger-deficit rows. It does
not drop intersection pairs. Core counts and holes are updated separately.

Every evaluation restores the original counts and selected flags. The driver
checks rollback by a direct family recount every 4,096 evaluations and at exit.

# Records, limits, and verification

The scan makes one pass, with no random seed, relaunch, or budget transfer.
It checks the 120-second elapsed-time limit before each replacement and handles
interrupt signals. The process watchdog is 135 seconds with a 5-second termination
grace. Completed means exactly 275,456 evaluations; every other outcome is
explicitly incomplete. No additional optimization is run after interruption.

Each strict improvement gets a record. All final ties at the best rank strictly
below the baseline are retained as complete outgoing/incoming descriptions.
The recorder reconstructs each distinct family, computes its canonical hash,
checks all counts and rows independently in Python, and sends it through both
the package verifier and the independent `scripts/check_cover.py` parser and
verifier. This direct standalone-module path avoids one process per compact
tie; the standalone CLI additionally checks the inputs and saved representative.
Every final tie has its full family hash and compact dual-verifier receipt in
the ignored raw candidate audit. One full representative is saved for inspection.

If the pass completes, the tied best result is an exhaustive statement about
this one-block-swap neighborhood under the listed necessary rows. If the pass
is incomplete, it is only the best observed result. Neither outcome supplies
a global infeasibility claim or a lower bound for the covering number.

# Controls and gate

The known prior CP move 3145→3752 takes the old legal H12/D2max 34 family to the
new legal H12/D2max 32 family. Its reverse is a legal neighbor of this scan's
start. Fixed sanitized controls check both directions and exact rollback.
A production-driver control with zero evaluated neighbors checks honest
incomplete output. A clearly labeled synthetic recorder fixture uses the real
positive family and its true enumeration ordinal to check saving and tie
reconstruction; it is not an executed scan prefix. Ten damaged recorder fixtures
are rejected, including false completion, bad counters, negative time, premature
timeout, wrong ordinal, wrong incoming block, and duplicate ties.

The independent gate additionally checks all 4,368 universe columns, all 120 pair
row groups, 50 fixed swaps spanning intersection sizes 0 through 4 and core-overlap
changes, 125,000 count comparisons, exact rollback, invalid operations, legality
and rank controls, and the independent recorder checks. The full enumeration
was not launched during preparation.

Frozen manifest SHA256:
`71c0586872f86f4b367cf410beb6718707266bc55463f84aaf095513ac601764`.
Producer controls SHA256:
`dfb9230591ab1a6c3e38614e91adac87ea0ae52395633525cc900ba8a050eaad`.
Independent GO gate SHA256:
`3f6247263cb75a0258357e2e356158388fad434e8b89bb6c9210f9871adc889c`.
Root owns the sole full pass:

```sh
uv run python experiments/2026-10-04/weak-pair-swap-scan/run.py \
  --gate experiments/2026-10-04/weak-pair-swap-scan-independent/gate.json
```
