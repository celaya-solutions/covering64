```
Document:    Cut-Pilot Heavy-Tuple Completion and LP Screen
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      d1b0e445af3aa5a41e9756d0336d3225007f0cc9ad493fb9121144f617884d54
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Completion screen for the cut-pilot heavy tuple

The frozen cut-guided pilot best has ten uncovered triples and SHA256
b48c3ce6653c92936ff824fc2d68e29b0ba080c985378c9c85b02418e6849c93.
Its four heavy template IDs are 13164, 13504, 5835 and 21941. It passes all
31104 relabelings of the preceding cut. Passing that cut orbit did not establish
that any full completion exists.

## Model and scope

The new model fixes only these 28 heavy blocks. It retains all 1200 ordinary
Boolean variables in original global lexicographic order and selects exactly 36.
Its 697 rows enforce all triple coverage, point degree 20, 114 proved anchor-pair
equalities, hub-pair bounds five through seven, and the proved upper bound two
on each nonheavy triple. All six possible hub graphs remain allowed; there is
no hint, objective or fixed ordinary block.

The builder reuses the already audited incidence matrix and shifts only its
bounds from the old heavy incidences to the new ones. Undoing those shifts
recovers the prior proto exactly. Source, model, pilot seed, oracle audit and
family-preservation gate are bound in manifest.json. Root independently rebuilt
all 697 rows and 1200 variables and rejected six damaged models; its receipt is
../cut-pilot-heavy-completion-independent/gate.json.

This is conditional on the regular degree-20 four-sevenfold family with the
specified four anchors and hubs. It is not the unrestricted covering model.

## Checked first-link membership

The screen classifies all four heavy links separately under every possible hub
graph, using the complete checked archive of 29970 labeled links per case and
the frozen registry of 109 proved exclusions. Both available graph transports
agree for every link. Explicit physical-to-representative permutations and
proof-source paths are saved in first-link-screen.json.

Five graphs are ruled out by the existing registry. Only graph index three,
with lexicographic hub excesses [1,0,1,1,0,1], has no closed link. Its IDs are
cycle-086, cycle-086, cycle-054 and cycle-099. This is a registry-membership
result, not a claim that any open representative is extendable.

## Cheap exact LP screen

After the root model gate and first-link screen, one feasibility LP and its
elastic diagnostic ran with GLOP 9.15.6755. The full six-graph relaxation was
used; no registry exclusion or particular hub graph was added. The feasibility
solve returned INFEASIBLE in 0.134177 seconds. The elastic solve returned an
optimum of about 12.6457 in 0.156510 seconds.

The saved 542 signed rational row multipliers use denominator 1000. Exact integer
replay gives right-hand side 12648 and ordinary-box maximum 108, hence gap
(12648-108)/1000 = 627/50 = 12.54. The numerical status alone is not the proof;
the exact signed-row certificate is dual.json and the runner record is
lp-result.json. A separate independent replay is handled by root.

All raw models, immutable source snapshots, solver values and receipts remain
in ignored experiments/scratch/cut-pilot-heavy-completion-v1.0.0 and
experiments/scratch/cut-pilot-heavy-completion-lp-v1.0.0. No timed CP search was
launched. No first-link registry or global covering bound was changed.
