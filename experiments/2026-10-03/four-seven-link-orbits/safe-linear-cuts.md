```
Document:    Certified Linear Cuts from the Complete First-Link Classification
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      1c7b7dafd4485f21b334b7d979d530cfb4d04127a48f4218be07b0cb2459a939
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Five rules transported to all four heavy groups

These inequalities hold for integer regular 64-block covers in the normalized
four-sevenfold branch. Their proof uses the complete link classification and
the separately checked LP infeasibility certificates. They need not hold for
all fractional points of the original relaxation.

For a chosen anchor triple A_i and its hub h_i, its seven common blocks have the
form A_i union e, where e is an outside pair. The link consists of those seven
pairs. The hub h_i has degree two, every other outside point has degree one,
and no pair joins two anchors within another anchor group.

Call two groups adjacent when their hub pair has positive excess: one of the
four cycle edges, or one of the two doubled matching edges. The following
counts refer only to the seven edges of the chosen link:

| Symbol | Edge predicate |
| --- | --- |
| H | Both endpoints are hubs |
| S | One endpoint is a hub, and the other is an anchor in that same group |
| A | Exactly one endpoint is a hub, and its two endpoint groups are adjacent |
| C | Both endpoints are anchors, and their groups are adjacent |
| D | Both endpoints are anchors, in distinct nonadjacent groups |

Each count is a linear sum of the variables x_(A_i union e) for edges satisfying
its predicate. H and S are disjoint predicates, so H+S is also a sum with only
unit coefficients. No auxiliary indicator variables are needed.

| Case | Necessary inequality | Violating base-link orbits | Labeled links |
| --- | --- | ---: | ---: |
| Cycle | A <= 3 | 14 | 3,132 |
| Cycle | D <= 2 | 4 | 162 |
| Matching | H + S >= 1 | 15 | 4,212 |
| Matching | A <= 2 | 9 | 1,998 |
| Matching | C <= 2 | 4 | 162 |

The violating sets can overlap. The table is not a partition of all exclusions.
The four transported copies yield eight new cycle rows and twelve matching
rows. Per group, the coefficient lists contain 18 and 9 terms for the cycle,
or 15, 9, and 9 terms for the matching, in the displayed order.

## Finite proof for the first anchor group

The complete independent orbit audit establishes exactly 29,970 labeled first
links in each case, partitioned into 129 orbits. Each orbit has explicit checked
representative-to-member maps and inverse maps. The first-group stabilizer fixes
points 1,2,3,4 and preserves anchor groups and the hub graph.

For each predicate, `derive_linear_cuts.py` counts its value on all 129
representatives and all 29,970 archived members. Every member's value equals
its representative's value. Every representative violating the stated bound
has a positive exact infeasibility gap in the independent final LP certificate
audit. The full audit covers all 258 cycle/matching representatives, and its
results hash is checked against the frozen screen.

If an integer cover violated one of the first-group inequalities, its first
link would belong to one of these violating orbits. Relabeling by the checked
inverse map would give a cover for its excluded representative. A separately
checked exact linear contradiction rules that out. Therefore the first-group
inequality is valid. This argument does not extrapolate an empirical
correlation; it exhausts every possible violating link.

## Transport to every heavy group

The weighted cycle and doubled-matching hub graphs each have eight group
automorphisms and are vertex-transitive. The derivation exhausts all 24 group
permutations, retains exactly the eight preserving every hub-pair excess, and
chooses a map taking group zero to each target group. The following maps use
zero-based group indices; each tuple lists the images of groups 0,1,2,3:

| Target group | Cycle map | Matching map |
| --- | --- | --- |
| 0 | (0,1,2,3) | (0,1,2,3) |
| 1 | (1,0,3,2) | (1,0,2,3) |
| 2 | (2,1,0,3) | (2,3,0,1) |
| 3 | (3,0,1,2) | (3,2,0,1) |

The corresponding point map preserves the offset within each four-point group:
the three anchor offsets remain anchors, and the hub offset remains a hub.
Thus it preserves the normalized pair counts, full coverage, cardinality,
regularity, and the heavy-triple structure. The derivation checks transport of
all 69 allowed outside edges and the selected predicate edges, in both
directions, for every target. The inverse point maps are saved explicitly.

A violation at any target group would therefore relabel to a first-group
violation. Applying a relabeling to a hypothetical cover is not a requirement
that the cover itself be invariant under that relabeling.

## Machine-readable rows and evidence

`safe-linear-cuts.json` is the implementation handoff. Each rule contains its
case, predicate, inequality sense, bound, exact violating representative IDs,
their checked gaps, all base representative values, and all four transports.
Each target contains the anchor triple, hub, group and point maps, inverse map,
and coefficient records with edge, five-block, global variable index, and
coefficient one. Point labels are one-based; group and block-variable indices
are zero-based. Variables follow the complete lexicographic ordering of all
4,368 five-subsets, without reordering or reducing that array.

The JSON hashes the derivation source, representatives, orbit map archive,
independent orbit audit, full LP results, and the final independent LP audit.
It can be regenerated with:

```sh
uv run python experiments/2026-10-03/four-seven-link-orbits/derive_linear_cuts.py
```

The certificate audit is
`../four-seven-link-lp-independent/full-v1.1.0-final-audit.json`.
The complete LP results archive hash is
`f96c156276584f72e6134aa2cd6a68cc81d1c0f1164f3cc205f240720cae4207`.

## Broader feature analysis and its limits

`analyze_lp_features.py` and `lp-feature-analysis.json` record all link feature
vectors and outcomes. The full screen excludes 27 cycle and 73 matching
orbits, leaving 102 and 56 numerically LP-feasible cases. No exact primal
witness or integer cover follows from those numerical statuses.

Fourteen simple edge and hub-leaf features take 95 distinct vectors in each
case. Five cycle vectors and seven matching vectors occur in both an excluded
and a nonexcluded orbit. Examples are cycle-006 versus cycle-019, and
matching-032 versus matching-041, respectively. These coarse counts therefore
do not fully explain the exclusions.

All ten representatives with H=2 pass the numerical LP in each case. That is
only a possible search-order clue. The separate primal-fractionality and
rounded-cover inspection should guide bounded CP trials; no other surviving
type can be discarded. This analysis ran no additional covering search.

The header hash covers the body after the header fence, including its initial
blank line.
