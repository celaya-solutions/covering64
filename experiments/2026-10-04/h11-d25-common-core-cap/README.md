```text
Document:    H11 D25 Common Core Overlap Cap
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      26c1c5cd0243b367b446a6d5941f2d226e6f6ff4149cd0445ca80c3278d4a467
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# A checked overlap cap for the new 62-block core

Every full covering with exactly 64 distinct blocks overlaps this pinned core
in at most **56 blocks**. This is an unrestricted conditional overlap bound:
no point degrees, pair profiles, old-core limits, orbit rules or construction
recipe are assumed. It is not a proof that a 64-block cover does not exist.

## Pinned inputs and direct checks

The source is the independent neutral-queue postcheck, SHA256
`fd044b1f88955403181b2d6ac739526c2d27ded14b0cff66f36a59d40a1cdde3`.
Exactly 28 of its distinct families have saved audited rank H11/D25. Their
full intersection is [core-62.txt](core-62.txt), with 62 distinct pentads and
SHA256 `c2190a6c9fdc0e0f5cc56c991b79c109925e1c3f7ea375ec353535c717415b72`.
Every family's canonical bytes, block IDs and hash were checked again; both
covering verifiers independently confirm its 64 blocks and 11 missing triples.
The D25 value is inherited from the pinned independent runtime audit.

The core misses exactly the 15 triples in [holes-15.txt](holes-15.txt).
Both covering verifiers independently agree on those holes and the core's
62-block cardinality. The core and all 28 source families are incomplete
covers, not successful 64-block witnesses. A separate full-universe positive
control passes both verifiers with all 4,368 blocks.

All 4,368 possible pentads, in global lexicographic order on labels 1–16,
were independently checked against all 15 holes:

| Holes covered by one pentad | Number of pentads |
| ---: | ---: |
| 0 | 3,253 |
| 1 | 1,060 |
| 2 | 55 |

The complete indexed list is [carrier-counts.json](carrier-counts.json).
No pentad contains three holes. As a separate combinatorial check, the 105
hole pairs have intersection histogram `{0:50, 1:55}`. Among the 455 sets of
three holes, union sizes are `{6:25, 7:214, 8:176, 9:40}`.

## Complete proof

Let K be the pinned core and H its 15 missing triples. Every block of K covers
zero members of H. Every possible pentad covers at most two members of H,
as checked over the full universe. Thus any full cover F must satisfy

`15 <= sum_{B in F outside K} |{T in H: T subset B}| <= 2*|F outside K|`.

Consequently at least `ceil(15/2)=8` blocks lie outside K. If |F|=64, then
`|F intersect K| = 64-|F outside K| <= 56`. Overlap 57 would leave at most
seven outside blocks, which can cover at most 14 of the 15 holes.

The maximum carrier count also has a short direct proof. Distinct holes
intersect in at most one point. For any three holes, inclusion-exclusion gives
union size at least `9-3=6`; their three-way intersection can only increase
that lower bound. Hence no five-point block can contain three holes.
Equivalently, weight every hole by 1/2. Every possible block has load at most
one, giving the exact rational lower bound 15/2, then the integer bound eight,
on the number of outside blocks. The receipt records this dual certificate.

Every permutation of the 16 points maps the complete block universe
bijectively to itself, preserving containment and intersection. Therefore the
same overlap bound holds for each relabeling of this core. This does not
assume that an arbitrary covering has any particular labeling.

## Use and verification scope

For an exact-64 model with all triple-cover constraints, the safe row is
`sum_{B in K} x_B <= 56`. It may be added for this fixed core, or separately
for any explicitly selected relabeling. The exact-64 cap must not be copied
unchanged to other live cardinalities: the general implication is
`|F intersect K| <= |F|-8` for a full cover F.

[check.py](check.py) reconstructs the pinned bank, the full intersection,
all holes and all 4,368 carrier counts without producer helpers or a solver.
Its valid certificate passes, and 17 malformed or altered controls are
rejected, including duplicate/damaged blocks, false holes, changed carrier
counts and weakened bounds. [certificate.json](certificate.json) records all
member hashes and IDs, verifier hashes, source revision, complete artifact
hashes, direct-count histograms, controls and the exact bound. Ruff passes.
No existing frozen experiment was changed.
