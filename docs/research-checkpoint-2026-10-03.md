```text
Document:    C(16,5,3) Research Checkpoint
Version:     v1.3.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      7977a56cf775bbbefb767a5182cc0bf511e07c1a03f67857dcc0e384eeeb2f1e
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# C(16,5,3) research checkpoint

The 64-block goal remains open. The best saved 64-block state covers 557 of 560
triples. Both cover verifiers reject it as incomplete. The known full cover uses
65 blocks. Current primary-source tables still report bounds 61 through 65.

## Checked restricted results

The Belic cover has a rigid 60-block core. Keeping it leaves 15 triples uncovered;
each possible added block covers at most three. Its five independent completion
supports each allow 12 fifth-point choices, giving 248,832 valid 65-block completions.
Two covers derived from C(17,6,4) are nonisomorphic as full covers but have this
same core up to relabeling; they do not establish a new search basin.

Exact rational LP dual certificates now rule out every 64-block completion
retaining at least 56 of the specified core blocks. A standard-library checker
verified 8,337 symmetry representatives covering all 487,635 four-block removal
sets. Its smallest exact lower bound is 2,035,711/250,000 (>8 additions). Thus any
64-block cover contains at most 55 of these 60 core blocks. The same inequality
holds for every relabeling of the core and is safe to add to the unrestricted
model. This necessary condition does not prove global nonexistence.

Check it with `python3 -I scripts/check_core_orbit_certificate.py
experiments/2026-10-03/core-orbit/core-remove-4.json.gz` on one shell line. The
compressed certificate SHA256 is
`9997df71457bd6f4ca5567032cd026e3956d29235515acc330f05fddc6d9c298`.
Earlier zero-, one-, two-, and three-removal certificates are retained too.

A restricted scan of 909 five-removal classes excluded 908 by exact dual weights.
The remaining class has an exact dual bound of nine and only 50 tight candidate
blocks. A three-block contradiction rules it out: coverage requires at least two
of the three blocks while their positive-weight overlaps allow at most one.
A separate standard-library exhaustive reconstruction also closed this kernel
in three search nodes. This settles those 909 scanned classes, not every possible
five-removal neighborhood. See the core-five-scan evidence and standalone checker.

Seventeen explicitly specified regular permutation actions were each checked by
enumerating all 226,387,980 four-orbit selections. No complete cover occurred.
The best actions covered 34 of 35 triple orbits (544 triples). This is neither a
classification of 17 distinct groups nor an unrestricted exclusion. An independent
reconstruction of all group actions and orbit masks agreed with the saved masks.

## Search and validation

Search tools now include weighted local search, fixed-link and neighborhood
CP-SAT searches, native-cardinality SAT, group-orbit enumeration, valid-cover
trade walks, and exact rational LP screening. LP screening rejects a neighborhood
only when independently checkable dual weights exceed its replacement budget.
UNKNOWN and timeouts are inconclusive. Ongoing campaigns and larger raw logs stay
in `experiments/scratch`; compact witnesses, controls, provenance and certificates
are retained here. No discovery was published and no researcher was contacted.

Saved test logs record the passing suite and its subtests. Compiler and proof
checker controls reject malformed and damaged inputs. The restricted search modes are
explicitly documented and are not imposed on the unrestricted model.

## Next search split

For any cover of at most 64 blocks, every point occurs at least 19 times. Thus
either every point occurs exactly 20 times, or one point has degree 19. In the
second case its 19-block, four-point link has fourteen vertex degrees 5 and one
degree 6. The pair-excess graph must be a four-edge star plus five disjoint edges.
This pattern can be normalized by relabeling without fixing an incumbent link.
CP-SAT and native-cardinality SAT searches treat these two exhaustive cases
separately and avoid incompatible degree ordering. Regular covers may normalize
a selected block to {1,2,3,4,5}. In the degree-19 case, at least one of the six
center blocks has at most one star leaf, yielding four canonical representative
block types. The optional disjunction preserves existence under the remaining
point symmetries.

Six bounded branch searches (CP-SAT, native SAT, and independent SCIP) finished
UNKNOWN or NOT_SOLVED after their 600- to 1,200-second limits. No complete cover
was found. Their models, versions, hints, source snapshots and compact results
are archived in completed-degree-searches.json.gz; full raw logs stay outside Git.
New CP runs add the separately checked core inequality. Targeted deeper repairs
use exact dual load filtering and weighted overlap bounds.

A regular 64-block near cover with exactly 20 occurrences of every point misses
five triples. A separate one-swap version also meets the necessary pair incidence
bound of five for every pair. Both independent cover checks correctly reject
them as incomplete. They are search seeds, not solutions.

## Independently replayed deeper neighborhoods

All 33 selected six-removal neighborhoods and all 100 selected seven-removal
neighborhoods are now excluded by complete search trees checked with a separate
standard-library program. The trees contain 133 and 491 nodes respectively.
The checker rebuilds all 4,368 blocks, all 560 triples, every dual capacity, the
complete reduced block pool, and every legal branch. It also requires coverage
of residual triples with zero dual weight. Eleven controls reject damaged
certificates, incomplete pools, duplicate inputs and incomplete searches.
These results apply only to the listed neighborhoods, not to every removal set.

The exact-search archive also contains the matching CP-SAT results and two
600-second global searches with independently checked core cuts. Both global
searches returned UNKNOWN. A known 65-block positive control passed both cover
verifiers. The general best remains 557/560; no 64-block cover has been found.

Evidence is in `core-six-independent`, `core-seven-independent`, and
`exact-search-campaigns.json.gz` under `experiments/2026-10-03`. Larger models
and raw logs stay in ignored scratch storage. New focused eight-removal scans,
broader objective-based repairs, and smaller cyclic families are being explored
separately from these completed results.

## Recovered four-link classification and a stronger regular branch

A new hub-graph enumeration reduced all normalized degree-19 links to206
structural cases. A separate standard-library search exhausted31,989 nodes,
and a third implementation replayed the complete trees. Exactly114 labeled
links survive, forming four isomorphism classes. All114 links pass both cover
verifiers at C(15,4,2). Two independent methods checked their relabeling maps.

This recovers the published four-class theorem of Allston, Buskens and Stanton
(1988), Theorem12, rather than establishing a new classification. Their designs
B3, B4, D1 and D2 map to our hub classes47,44,4 and1. The first two had already
been searched; the latter two supply new extension cases for this project.
Both fresh target64 runs returned UNKNOWN after300seconds. The four fixed-link
extension families together cover the degree-19 branch up to relabeling.

The regular branch now also has a safe point-essential restriction: each
selected block-point incidence must support a private triple. Otherwise an
elementary point replacement gives a degree-19 cover, already included in the
other branch. Separate exhaustive controls check the CP encoding and the
relabeling normalization. A bounded partial-cover search returned UNKNOWN;
full CP and native SAT searches are separate ongoing work. See
`docs/degree-branch-reduction.md` for the complete derivations and scope.

Other completed searches found no64 cover: twelve bounded cyclic-family CP
runs returned UNKNOWN, four orbit tabu pilots remained incomplete, and a
600-second broader repair search failed to improve on three missing triples.
All near3 states in that repair wave retained the same60 core blocks. The155
focused eight-removal kernels returned CP-SAT INFEASIBLE; their exact LP inputs
and reductions were independently audited, but those solver statuses alone
are not independently certified nonexistence results.
