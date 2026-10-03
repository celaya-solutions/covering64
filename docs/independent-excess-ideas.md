```text
Document:    Independent Excess Profiles for C(16,5,3)
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      7dadce904ac4b9dd7fec6cdcb7b104f24dd32eaeb6ddf71feaba9bff266b22a3
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Scope and evidence

This is a new restricted construction route through the excess triples. It does
not classify all 64-block covers or exclude any complete degree branch. No
covering-design solver was run while deriving or checking this note. The profile
generator produces triple multiplicities, not a covering witness. A resulting
64-block family must still pass the package verifier and `scripts/check_cover.py`.

Context was read from `docs/recovery.md`, both current research checkpoint
documents, `docs/degree-branch-reduction.md`, and the frozen
`experiments/2026-10-03/independent-geometry/other-session-checkpoint-readonly.md`.
The last snapshot reports an incomplete 557/560 partial cover and ongoing
sevenfold-triple constructions. Nothing here uses their local-link templates,
their 13-point family classification, or an incumbent block family. Missing
historical artifacts were not reconstructed. The derivations below are elementary
and self-contained; no external theorem or novelty claim is required.

# 1. Excess variables

Assume a regular family of 64 distinct five-point blocks on 16 points, with
every point in 20 blocks. Write `lambda(uv)` for pair multiplicity and `mu(T)`
for triple multiplicity. In a cover, `lambda(uv) >= 5`. Define

    e(uv) = lambda(uv) - 5,
    h(T) = mu(T) - 1.

Direct incidence counting gives

    sum_v e(uv) = 5,
    sum_T h(T) = 80,
    sum_{T containing u} h(T) = 15,
    sum_{T containing uv} h(T) = 1 + 3 e(uv).

For example, a pair has 14 possible third points and each block through it
supplies three; hence its excess-triple sum is `3 lambda(uv) - 14`.

One possible restricted baseline takes `e` to be the adjacency matrix of a
simple 5-regular graph E. Pair multiplicities are then 6 on E and 5 elsewhere.
Even before selecting blocks, seek a nonnegative integer triple family H with
pair degrees 4 on E and 1 elsewhere. Its point degrees and total size follow
automatically from these pair degrees. The ordinary divisibility conditions for
the eventual five-block decomposition already hold: triple mass 640 is divisible
by 10, point mass 120 by 6, and pair mass 15 or 18 by 3. These elementary
congruences alone cannot reject such a profile. No general integer-lattice
sufficiency theorem is asserted here.

# 2. A triangle-free graph forces the shape of every excess triple

If E is triangle-free, every triple contains at most two E edges. Count E-edge
incidences in H, with multiplicity:

    sum_T h(T) * |E[T]| = 40 * 4 = 160 = 2 * 80.

Equality forces every triple with positive excess to have exactly two E edges.
Thus it is an induced three-vertex path. Its endpoints form a nonedge of E,
whose required excess pair degree is one. Therefore `h(T) <= 1` automatically.
The assumptions `mu <= 2` and simplicity of H are consequences in this slice,
not extra restrictions. Each nonedge chooses exactly one of its common neighbors
as the center of its unique excess path. In particular E must have diameter two.

At every vertex, exactly five H paths are centered there and ten have it as an
endpoint. The endpoint count is ten because there are ten nonneighbors, each
requiring exactly one path. Its five E edges have H pair degree four, giving
20 incident E-edge occurrences; subtracting the ten endpoint occurrences leaves
five centered paths.

# 3. The Clebsch graph makes the choices explicit

Use the 16 even-weight binary words of length five, in increasing integer order,
as labels 1 through 16. Two labels are adjacent when their binary words differ
in four coordinates. Its five generators are

    g_i = 31 XOR (1 << i), i = 0,...,4.

Each has weight four; their sum over F2 is zero. A sum of two distinct generators
has weight two. Consequently E is 5-regular and triangle-free. Every nonedge has
difference `g_i + g_j` for a unique pair of generators, and its two common
neighbors are obtained by adding `g_i` or `g_j`. This proves the required
Clebsch parameters `(16,5,0,2)` directly for the labeling used by the code.

For each generator pair there are four squares

    {x, x+g_i, x+g_j, x+g_i+g_j},

so there are 40 squares in all. The two diagonals of each square are nonedges.
Their two center choices select two of its four path triples. Those two triples
have a unique common E edge: that edge is used twice, its opposite edge zero
times, and the other two edges once. Thus a square can be described by selecting
one positive edge and declaring its opposite negative.

Every E edge belongs to four squares. Its target H pair degree is four, so the
positive and negative deviations at each edge must balance.

# 4. Exact auxiliary description, and a constructive subfamily

Make an auxiliary graph whose 40 vertices are the E edges. Each square offers
two choices of auxiliary edge, one for each pair of opposite sides. Select one
choice per square and orient it from the negative E edge to the positive one.
The balance condition is exactly equality of indegree and outdegree at every
auxiliary vertex. This description is equivalent to every admissible H for this
fixed Clebsch pair profile. It does not yet choose any five-point blocks.

The full auxiliary graph is five disjoint copies of K(4,4), one for each
generator direction. For a fixed generator, E edges are cosets of its span.
The other four generators induce four translations on the resulting F2^3;
they sum to zero and any three are independent. These are precisely the four
odd-parity translations, giving K(4,4).

A convenient subfamily needs no search:

1. Choose a regular tournament on the five generator directions, so each
   direction wins against exactly two others.
2. For every square of directions i and j, select its pair of opposite sides
   in the winning direction.
3. Each auxiliary component now has degree two: two disjoint four-cycles.
   There are ten such cycles across all directions. Orient each cycle either way.
4. For each square, put in H the two triples containing its positive edge.

Each auxiliary vertex has one incoming and one outgoing edge. Its deviations
cancel, proving every E edge has H pair degree four. Each square diagonal has
H pair degree one by construction, and diagonals belong to unique squares.
All 80 output triples are distinct because an induced path belongs to a unique
square. This proves all required profile counts without a covering solver.

There are 24 labeled regular tournaments on five directions: for one fixed
direction choose its two outneighbors in six ways, orient their mutual edge in
two ways, and orient its two inneighbors' mutual edge in two ways. Requiring
outdegree two then fixes all remaining edges. Every such tournament is a
relabeling of the cyclic one. For each, the ten
independent binary orientations yield 1,024 different profiles. Different
tournaments give disjoint profile sets because a profile determines the winning
direction of every square. The construction therefore gives exactly 24,576
labeled profiles. It does not give all Clebsch profiles: an admissible auxiliary
selection need not choose the same direction for all four squares of a given
generator pair, or have auxiliary degree two at every vertex.

# 5. Sixteen representative profile tests suffice for this subfamily

The Clebsch relabelings include all 16 translations and every permutation of the
five bit coordinates. All 24 regular tournaments are equivalent under coordinate
permutations, so fix the cyclic tournament with direction order `(0,1,2,3,4)`.
Its remaining preserving actions are the 16 translations and five cyclic
coordinate rotations, giving 80 explicit maps.

An exhaustive arithmetic enumeration generated all 1,024 orientation choices,
applied these 80 maps, checked closure, and removed complete orbits. It obtained
16 orbits: twelve of size 80 and four of size 16. Their sizes sum to 1,024.
Accordingly the following seeds of `make_profile` cover the whole 24,576-profile
construction up to a Clebsch relabeling:

    0, 1, 9, 40, 19, 8, 4, 18, 16, 12, 3, 10, 11, 26, 60, 25

The enumeration normalized each seeded tournament by mapping its shuffled
direction order back to `(0,1,2,3,4)`. The table uses the generator's sorted
auxiliary-component order; bit k reverses cycle k.

| Orbit | Fixed-tournament orientation bits | Orbit size | Seed |
| --- | ---: | ---: | ---: |
| 0 | 163 | 80 | 0 |
| 1 | 675 | 80 | 1 |
| 2 | 35 | 80 | 9 |
| 3 | 547 | 80 | 40 |
| 4 | 419 | 80 | 19 |
| 5 | 931 | 80 | 8 |
| 6 | 291 | 80 | 4 |
| 7 | 803 | 80 | 18 |
| 8 | 3 | 16 | 16 |
| 9 | 387 | 80 | 12 |
| 10 | 899 | 80 | 3 |
| 11 | 259 | 80 | 10 |
| 12 | 739 | 80 | 11 |
| 13 | 995 | 16 | 26 |
| 14 | 130 | 16 | 60 |
| 15 | 866 | 16 | 25 |

These 16 representatives are sufficient for this construction even if additional
automorphisms were later found to merge some of them. The complete record and
replay program are saved under
`experiments/2026-10-03/independent-geometry/profile-orbits/`. The JSON certificate
contains 1,024 profile hashes, all 80 explicit point maps, the full orbit
partition, and a map sending each profile to its stated representative. It also
records normalization maps for the seeded representatives. A separate checker
has now reconstructed all profiles, group maps, orbits and seed maps without
importing the producer. The scope is still the tournament recipe. This is not
an exclusion certificate for the block-decomposition problem.

# 6. Bounded block-decomposition experiment

For each selected profile H, set the exact required multiplicity of every triple
to `1 + indicator(T in H)`. Seek 64 distinct five-point blocks whose ten-triple
incidence vectors sum to this demand vector. This can be run as exact multicover
search on the usual 4,368 columns, with residual capacities one or two, rather
than as an unrestricted inequality covering problem. A row of residual capacity
one gives strong branching and overlap deletion. Pair and point equalities are
redundant checks or pruning constraints, not assumptions beyond the fixed H.

Any resulting decomposition automatically has pair multiplicities 5 or 6 and
point degrees 20: pair triple mass is three times pair block count, and point
triple mass is six times point block count. Total demand 640 forces 64 blocks.
Binary block selection enforces distinctness. No rotational or translation
invariance is imposed on the selected blocks. A solver may also be used for this
exact decomposition, but changing software is not the mathematical contribution.

A cheap first test is the 16 listed profiles with a fixed short time budget per
profile. Record each profile hash, all solver settings and source revisions.
An UNKNOWN result says nothing about that profile. A solver INFEASIBLE result is
only a restricted solver result until supported by a separately checked proof.
Even complete checked rejection of all 16 profiles would reject only the
regular-tournament construction, not all Clebsch profiles and not all covers.

If this construction is unproductive, enlarge the auxiliary choice space while
keeping the same small balance equations: choose one opposite-side pair per
square, require even auxiliary degrees, and choose Eulerian orientations. This
retains the exact characterization of all Clebsch H without returning to link
gluing or fixing blocks from the known 65-block cover.

# 7. Implemented generator and arithmetic checks

`scripts/independent_clebsch_profiles.py` exposes
`make_profile(seed: int) -> list[tuple[int,int,int]]`. It uses only the standard
library and returns lexicographically sorted triples with 1-based labels.
Different seeds may give the same profile; seeded sampling is neither uniform
nor complete. Its canonical source-body SHA256, excluding the nine-line comment
header and the following empty line, is

    dac4b562fe6162aecb680e38bf81f4dce3051abc53f8892a4ab5b0726deaa3cd

A separate arithmetic recount of seeds 0 through 999 checked 80 distinct sorted
triples, all 120 pair codegrees, all 16 point degrees, the induced-path condition,
and the five centered paths per point. All checks passed; these seeds produced
976 distinct labeled outputs. Four invalid seed controls (`True`, `1.5`, `"1"`,
and `None`) were rejected. No SAT, CP, MILP, or cover solver was invoked.

Profile hashes below use one sorted triple per line, integer labels separated by
one ASCII space, with a final newline:

| Seed | SHA256 |
| --- | --- |
| 0 | `35929823fbf6baa4de9446ca764aa11ce6379b691fecbe281f03ec02769cf8c0` |
| 1 | `7fcc8f169a806cfea1f37a3460b15f9786b61c4fb40ddef24292ab00b3e1f728` |
| 17 | `ade2a75f84d8376c53bdce25d920b090a7924c7c30b12e76b25cef331f74c625` |
| 999 | `c3e02e629e7c865c42f6d097f27ba2d343bca7a16ba5ad31dbaf6447f4c24f75` |

The base source revision was `c31aea40bb52dddd43532e91c3d62558fcf25cde` and the
arithmetic checks used Python 3.11.9. The saved orbit enumeration can be rerun with

    python3 -B experiments/2026-10-03/independent-geometry/profile-orbits/enumerate.py

It regenerates `certificate.json` beside the program, including source hashes
and its parameters. The certificate's canonical body SHA256 is

    9c1ef64b3ff11736d87bc5636fb8cd5aabad58996b8d20ec9cf54b7e83fe8384

Canonical body means compact, key-sorted UTF-8 JSON of the `body` object followed
by one newline. Independent replay passed, including damaged-certificate
controls with repaired outer hashes. Targeted Ruff checks of the generator and
enumerator pass. Root owns the
full package checks and any actual decomposition experiments. This subtask made
no commit, ran no cover solver, and contacted no researchers.
