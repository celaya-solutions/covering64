```text
Document:    Refreshed Template Hull from 106 Checked Exclusions
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      c36e8ee7eba6d515c42479abde1fa9506784f9c1620f3d7faa4b62beebf4f32b
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Template-hull refresh after 106 checked exclusions

This new catalog version uses the independently preserved 106-ID first-link
exclusion union. It keeps all original-100 artifacts intact. Its complete
catalog/matrix audit is a separate prerequisite for any new solver run.

| Case | Surviving orbits | Old templates/group | New templates/group | New LP variables |
| --- | ---: | ---: | ---: | ---: |
| Cycle | 102 | 25,020 | 25,020 | 104,848 |
| Matching | 50 | 14,202 | 12,690 | 55,528 |

The matching catalog loses 1,512 labeled templates per heavy group (10.65%).
The six removed orbit families have sizes: `matching-017` 216,
`matching-032` 432, `matching-038` 216, `matching-051` 432,
`matching-077` 108, and `matching-083` 108. Four groups therefore lose 6,048
weight variables. The matching extension has 406,356 nonzero coefficients;
including the unchanged base, the full matrix has 496,160. Cycle catalog and
matrix files are byte-identical to their originals.

## Exact construction and completeness argument

The builder filters the original complete base-group catalog by independently
checked orbit IDs. It preserves lexicographic template order and reindexes only
the retained template-weight columns. The first 4,768 columns and all 4,270 base
rows stay unchanged. It preserves all 280 extension row meanings: one simplex
and 69 heavy-block marginal equalities per group. Every remaining template
column has one simplex incidence and seven marginal incidences. There are still
4,550 rows and every variable remains in `[0,1]` for the LP.

For any integer cover in the normalized regular case, each heavy group's seven
blocks form one labeled link. The original complete classification places that
link in an orbit. A hub-graph automorphism moves the group to the first group,
preserving the normalized branch. Membership in a removed orbit would then
contradict that orbit's checked certificate (or its exhaustive six-case union).
Consequently every heavy group must use a retained template. Assigning weight
one to those four templates extends every such integer cover to this model.
This argument does not require the cover to be invariant under any automorphism.

For each of the four groups, the builder checks every forward and inverse
transport and compares the full transported set under both possible hub-graph
automorphisms sending the base group there. This gives 100,080 retained cycle
transports and 50,760 retained matching transports, with inverse checks and
alternative-map set equality. The saved group catalogs make the entire labeled
sets available for independent readback. A separate checker must reconstruct
survivors from the complete orbit archive, check all rows, and reject damaged
controls before this version is used for solving.

The new exclusions were proved using earlier, less restricted models. Applying
them to a later catalog is therefore not circular. Further pruning can proceed
only after any new exclusions have their own independent certificate replay and
an updated preserved proof union.

## Frozen evidence

- Exclusion union: `../four-seven-template-hub-independent/combined-first-link-exclusions.json`.
- Union SHA-256: `dc1f0790d593238d00c8eff3ac58753d70a7fc9c6820d73d0bb835569ac9fd0e`.
- New manifest SHA-256: `84183ee44ed2916ffd18d64b5f113774e4eda47bad5e82c6c79b1b3a64db5bdf`.
- Builder SHA-256: `e27a3d8cf1ff26d991082534df759218d00fe0cc777aea3c673249fbc3de6031`.
- New matching catalog SHA-256: `8a715fd88ef51f31662c6026a0575c72f1a9ffd610ba476a356de12c77fefff5`.
- New matching matrix SHA-256: `ee2072837ae28bcce599c60975995a5c88b3fc3eb635352abc089b3eb6d78bab`.
- Raw output: `experiments/scratch/four-seven-template-hull-refresh-106-20261003/`.

The raw directory contains frozen source, exclusion union, base catalogs,
complete four-group catalogs, matrices, and provenance. The manifest records
all cited proof-file hashes and the source revision. The build took 3.491 wall
seconds. Large catalogs and matrices remain out of Git.

## Bounded next experiment

No refreshed-hull solve has launched. Once the independent audit passes, first
try a case-wide matching LP. If it remains numerically feasible, screen the 50
remaining matching first-link representatives. At 15 total solver seconds per
model, including each optional phase-one solve, that is at most 765 requested
solver seconds (12 minutes 45 seconds), plus construction, validation, exact
certificate arithmetic, and file writing. Based on the prior matching screen,
a sequential run may be materially shorter, but its runtime is not guaranteed.
The cycle matrix is unchanged, so an identical cycle-only rerun adds no new
information. A Boolean-selector CP formulation can also use this catalog once
its exact integer encoding is independently audited.

This remains a necessary model for the regular branch. Numerical feasibility
is not a cover; timeouts are inconclusive; and no unrestricted lower bound is
claimed. Every positive contradiction requires an independent replay. No
external publication or researcher contact is part of this experiment.

Independent reconstruction now passes in `independent-audit.json`. The checker
reads the complete original orbit archive and the checked 106-ID proof union;
it does not import the refresh builder. It reconstructs both complete surviving
catalogs, all four transported catalogs per case, both valid hub transports per
group, and every simplex and marginal row. All original base rows stay intact.
Sixteen damaged catalog, map, row, width and bound controls were rejected.
This audit authorizes use of the refreshed models; it reports no solver result.
