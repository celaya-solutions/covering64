```
Document:    H6 Anchored Pair Repair Independent Finite Review
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      5744a6acce02ce22862da7e4d7ac554254395516a9b62a8e687daee5a5d4021b
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# H6 anchored pair repair: independent finite review

The producer profile passed an independent full recount. The checker imports no
producer code and launches no optimizer. It verifies all five family files with
the package and standalone verifiers, reconstructs all profile counts directly,
and rejects 12 damaged reports.

The H6 family has exactly three short pairs: {4,6}, {5,6}, and {10,12}, each with
count four. Any single added block that repairs all three must contain their
five-point union, so B*={4,5,6,10,12} is unique. Removing a block cannot help any
short pair. All 64 possible removals after adding B* leave at least one short
pair. Thus no exact one-swap repair reaches pair floor five.

For an exact two-swap repair containing B*, the checker enumerates every one of
the C(64,2)=2,016 drop pairs. After B* and both drops, 733 cases have a pair deficit
of at least two, which one more block cannot repair. Another 1,280 cases have
deficient-pair endpoints spanning more than five points. The remaining three
cases force exactly five points and therefore one second addition apiece. Each
addition is absent from the original family and distinct from B*.

| Second addition | Holes | D2max | D2sum | D3 | D4 |
| --- | --- | --- | --- | --- | --- |
| {2,6,13,14,16} | 11 | 23 | 48 | 1 | 0 |
| {3,6,11,14,16} | 9 | 21 | 38 | 1 | 0 |
| {6,8,14,15,16} | 11 | 23 | 48 | 1 | 0 |

All three have pair floor five and named overlaps [0,2,2,1,0,0], but all fail the
same single D3 condition: pair {6,9} has count five while triple {6,9,10} has
count three. None is weak-qualified. D2sum is metadata, not the ranking rule.

Adding B* without dropping anything gives 65 blocks and three holes. It remains
partial, is distinct from the complete 65-block baseline, and receives a null
exact64 cap verdict. The checker verifies this distinction.

This is complete only for the stated one-swap test and B*-anchored exact
two-swaps. It excludes neither unanchored two-swaps nor larger neighborhoods,
and gives no conclusion about unrestricted existence.

Run `uv run python experiments/2026-10-04/h6-anchored-pair-repair-independent/check.py`
in a reproduction checkout with the existing review receipt preserved elsewhere.
The checker refuses to overwrite its receipt. The first successful replay before
formatting is preserved, with its source, in ignored scratch; the tracked receipt
is from the final formatted source. Ruff passes.
