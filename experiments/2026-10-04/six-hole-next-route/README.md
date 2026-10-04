```text
Document:    Next Route from the Four Profile-Qualified Six-Hole States
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      bd429f76797dd9af6297dc41ee049ff2ecc958aa6ca54bebcb47f3595ae7e6dd
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Solver-free assessment

The four independently checked six-hole states use 72 distinct blocks together.
Their twelve distinct missing triples have 720 carriers in the full block
universe. Adding these carriers to the previous 277-block elite pool gives a
952-block adaptive pool. Adding every one-point replacement of a block in the
four-state union instead produces 3,409 blocks when combined with the hole
carriers, or 3,453 with the previous elite pool. This is already close to the
full universe of 4,368 blocks, so a separate one-point-expanded case is not
recommended before directly comparing the adaptive pool and full universe.

`inspect.py` exhaustively counted 275,456 distinct one-block replacements from
each state. The elite callback state has four strict improvements; the other
three states have fifteen each. Every strict improvement enters a forbidden
five-heavy profile. Thus none has a globally profile-eligible one-block
improvement. This is only a complete one-exchange enumeration from these four
saved states, not a bound for larger neighborhoods or covering designs.
`assessment.json` binds the source and input hashes, full adaptive pool, counts,
and every strict-improvement exchange. It made no optimizer calls.

# Prior methods checked

- The earlier unrestricted filter-and-fan beam repair admitted all 4,368 blocks
  and all 64 mutable slots. In 60 seconds it changed a five-hole state to three
  holes in one replacement, then retained a relabeled copy of the forbidden
  60-block core. See `../five-hole-unrestricted-repair/README.md` and `run.py`.
- Forced-novelty phases inserting 8, 16 or 32 blocks outside an elite pool,
  followed by tabu repair, produced twelve labeled three-hole states. All kept
  the original core and forbidden profile. See the forced-novelty section in
  `docs/research-continuation-2026-10-03.md`.
- The earlier `experiments/2026-10-03/heavy-profile-neighborhood/run.py` already
  separated newly observed forbidden partitions and repaired neighborhoods with
  8 to 28 mutable blocks. Dynamic profile separation is not a new algorithm here.
- The prior general heavy-profile heuristic also reached six holes. Another seed
  or longer unrestricted repair alone would not establish methodological novelty.

# Prepared follow-on

The separately frozen `../six-hole-pool-release/` pilot compares the 952-block
adaptive pool with all 4,368 blocks. Both release all 64 slots, retain the two
existing core-at-most-59 rows and two proved partition cuts, and use the same
checked elite final six-hole hint. The objective is 65 times the number of holes
plus overlap with the original 60-block core. Since core overlap ranges from zero
to sixty, one fewer hole always wins; the extra term only orders equal-hole states.
There is no new overlap cap, fixed heavy family, degree restriction, or radius.

The proposed matched budgets are 120 seconds per case, four workers, and the same
seed 2026104101. A new forbidden partition found afterward must be recorded rather
than silently triggering another solve. The frozen preparation still requires an
independent gate and explicit launch authorization. The change being tested is
adaptive hole-carrier expansion versus full release from new checked seeds, not
a claim to a new search algorithm.
