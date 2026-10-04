```
Document:    Independent Check of Seven Affine Completion Contradictions
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      080714f8e63e94b9f45fa7d1f714c88a1c59c1addfc43aa08b1bc9f8dc359197
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

All seven supplied finite contradiction certificates pass independent replay.
The checker rebuilds the complete residual systems directly from the actual
pinned twenty-block partials and their exact audited excess profiles. It uses
standard-library integer bitsets and does not import or call the producer's
propagator, any optimizer, or any search procedure.

The seven results exclude only these exact pinned partials with their exact
excess profiles. Combining them with the previously checked 249 exclusions
accounts for all 256 specifically saved affine point links. The checker
verifies that the seven residual cases are precisely the earlier survivors,
with identical partial hashes, and that the entire collection contains each
of the sixteen profile seeds paired with each of the sixteen points once.
This does not exclude other affine label maps, other local decompositions,
an entire profile, or unrestricted 64-block existence.

## Independent row reconstruction

For each case, strictly validate twenty distinct five-subsets on labels 1..16,
all containing the pinned point. Verify canonical bytes, file pins, and the
exact profile against the original audited profile inventory. Both existing
cover verifiers independently confirm twenty blocks, 185 covered triples,
and 375 holes for every partial.

Subtract partial triple multiplicities from 1+1_H on all 560 global triples
in lexicographic order. All residual demands are nonnegative and sum to 440.
The 105 point-containing rows have zero demand. Enumerate all 3003 pentads
avoiding the point, retaining their zero-based global lexicographic block IDs.
Build all 560 incidence masks from scratch, then append the exact cardinality
row requiring 44 selected blocks. There is no prior support pruning in this
reconstruction and no dependency on the CP model's encoding.

## Replay rules

Each trace row must list exactly its currently unassigned variables, with
strict integer IDs, no duplicates, and no variables outside the domain.

- A row already containing its exact demanded number of selected variables
  forces every remaining variable in that row to zero.
- A row whose selected and unassigned variables together exactly equal its
  demand forces every remaining variable in that row to one.
- A row contradicts its demand if too many variables are selected or too few
  selected and unassigned variables remain to meet the demand.

Each positive assumption must name a currently free variable. Its supplied
trace must reach a checked contradiction. Because variables are binary, the
assumed variable is then zero in every possible completion of the current
base state. The checker removes it, replays the supplied base trace, and
continues. It compares the complete final selected and removed sets and
checks the final contradiction directly. It does not seek new assumptions
or perform an optimizer call.

## Results and controls

| Case | Profile seed | Point | Failed positive assumptions | Force steps | Final triple | Required | Selected | Free |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0 | 10 | 5 | 166 | 2,4,8 | 1 | 0 | 0 |
| 2 | 40 | 13 | 8 | 161 | 2,14,16 | 1 | 2 | 4 |
| 3 | 4 | 7 | 4 | 129 | 2,10,14 | 1 | 0 | 0 |
| 4 | 18 | 3 | 6 | 137 | 1,12,14 | 1 | 3 | 1 |
| 5 | 16 | 3 | 7 | 154 | 13,14,16 | 1 | 0 | 0 |
| 6 | 16 | 8 | 4 | 113 | 1,12,15 | 2 | 0 | 1 |
| 7 | 60 | 3 | 10 | 209 | 5,9,16 | 2 | 0 | 1 |

In total, 44 failed positive assumptions and 1069 forcing steps pass. All 43
damaged controls are rejected, including wrong forcing values, omitted and
duplicate variables, invalid row and variable IDs, false contradiction rows,
already-removed assumptions, reversed failed-literal signs, damaged branch
and final states, missing closure, and malformed or duplicate input families.
The original certificate files are never modified by these controls.

Run `uv run python experiments/2026-10-04/clebsch-affine-completion-certificate-independent/check.py`.
The full audit saves every failed assumption's contradiction details, all
final contradictions, control outcomes, input pins, and the exact dependency
on the prior independent finite screen. `files.json` hashes the frozen audit
folder. The checked producer certificate SHA256 is
`935783a788c93d79046bf9599af2d95735e5ce087a43c876a6516acfbcfc7841`.
The prior independent 249-case screen SHA256 is
`8c7fd636138ee781dc308ce04c1eee47da63345b0eb3805a611ae794a43ab6a3`.
These conclusions rest on finite replay and arithmetic, not solver status.
