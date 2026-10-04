```
Document:    H6 Exact-Distance-Four Prefix Pilot
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      2b7a34fda79a1a66b74a7350be6cec7a90df659d3a75838b818d75b74795a56a
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# One prepared exact-distance-four search

This sibling extends the frozen strict-hole radius-three enumerator to exactly
four replacements. It skips distances one through three, retains all 635,376
original four-deletion sets, and targets H<=5 from the pinned raw H6 family.
Original nonmembers are the only additions, so every family has exact distance
four, exact cardinality 64, and distinct blocks. Labels are 1-based and global
block IDs retain lexicographic order. No earlier source or result is changed.

Only the parent may launch, after an independent gate bound to the manifest.
There is one single-process run, a 59-second internal limit, and a 60-second
watchdog. There are no retries, budget transfers, or stop-on-candidate shortcuts.
Every provisional candidate is persisted, then checked by both cover verifiers.
Pair, weak, and six named core conditions are postclassification only.

## Complete pruning argument

For a fixed deletion set, let U be the uncovered triples and let demand=|U|-5.
The sum of the four largest individual addition scores is an upper bound on
any four-addition union. Each member of a successful four-tuple must individually
score at least demand minus the three largest global scores. These are the
unchanged initial bounds from the deletion screen.

After an ordered prefix, let M be its covered subset of U, let r be the number
of additions still needed, and let D=demand-|M|. For every eligible remaining
tail block b, recompute gain(b)=|coverage(b) intersect (U minus M)|. Any successful
completion has total new union gain at most the sum of its individual gains,
which is at most the sum of the r largest tail gains. If that upper bound is
less than D, the entire prefix can be removed safely. Every member of a valid
completion must also have gain at least D minus the largest r-1 tail gains;
otherwise even the overestimate for its other members cannot reach D.

The recursion retains only tail members meeting that necessary floor, in their
original increasing order. An ancestor floor is necessary for each member of
every successful completion, so retaining its filtered tail loses no successful
tuple. Choosing only later tail positions makes every unordered exact-four set
appear once. If D<=0, the floor is zero and all remaining exact-distance-four
completions remain available; success is not an early stopping rule.

Residual masks have at most 46 bits here. Each leaf uses exact union popcount.
The original zero-crossing coverage restoration and candidate-write-before-ledger
sequence are retained. Timer interruption keeps the shell incomplete even if
the final deletion set had already been entered. Interrupted or partial output
is retained, and no timeout is reported as a negative result.

## Scope and preparation evidence

The completed deletion screen leaves 2,168 initial pools. Its frozen histogram
bounds the number of two-adder prefixes by 1,012,567 and their ordered-tail gain
evaluations by 56,485,156, before stronger pruning. Later prefix work can still
be substantial; preparation does not claim that the search will finish in 60
seconds. No actual-H6 replacement prefix or tuple is explored during preparation.

Author controls use only v7 fixtures and an independent unpruned Python oracle:
four-block fixtures with 2,380 exact-four exchanges each produce respectively
1,554 and zero accepted families; a five-block fixture checks 9,100 exchanges
across five deletion sets and produces 43 accepted families. Controls also reject
duplicate, malformed, unsorted, out-of-range, extra-label, wrong-hole-count, and
NaN-budget inputs, and check that a zero budget remains incomplete. Candidate
families, exact symmetric differences, holes, and uniqueness are compared in full.

All source, binary, inherited verifier/classifier dependencies, input, earlier
radius-three result, and deletion-screen evidence are pinned by the manifest.
Its source revision records the actual HEAD at preparation. Large binaries and
fixture artifacts stay in ignored scratch space. Prefix-node, safe-pruning,
gain-evaluation, deletion, leaf, and candidate counters are saved separately;
leaf counts refer only to tuples reached after safe prefix filtering.

This is one local neighborhood. Even a completed result says nothing about
unrestricted existence. The root-owned launch command is
`uv run python experiments/2026-10-04/h6-strict-hole-radius4-prefix-pilot/run.py --gate PATH_TO_GATE`.
