```text
Document:    Independent Affine Extension Point Variant Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      5850334bdd383f9056f92eeec96783703c082e0c88d85ec611836c7cdcb963eb
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent finite variant audit

The independent replay found all 675 settings in the four fixed ray-target
recipes, grouped into 161 orbits under their complete excess-graph automorphism
groups. Exactly 157 orbits are outside the four previously chosen witnesses'
orbits. There are 651 individual settings outside those old orbits. No producer
code was imported, and no optimizer was called.

| Fixed recipe | Valid settings | Full graph group | Orbits | New orbits |
| --- | ---: | ---: | ---: | ---: |
| C4-leaf | 162 | 96 | 54 | 53 |
| C5 | 243 | 320 | 17 | 16 |
| triangle-path2 | 162 | 96 | 54 | 53 |
| triangle-two-leaves | 108 | 144 | 36 | 35 |
| Total | 675 | — | 161 | 157 |

## Finite completeness and independent checks

Each recipe has five extension positions with three choices each. The checker
independently enumerates all 243 choices per recipe, or 972 total. It rejects the
297 choices with repeated extension centers only after directly checking that
their excess graph contains degree-seven vertices. The four target graphs have
only degree-one and degree-four vertices, so those choices cannot belong to the
stated classes under relabeling. This establishes the scope of the 675 retained
settings without assuming the producer's filter is safe.

For every retained setting, the checker reconstructs all twenty blocks, checks
all 105 exact pair demands and all 455 triple caps, verifies the saved graph
isomorphism, and computes an independent orbit minimum. It checks each explicit
setting-to-representative map, every saved membership index, and old-witness
membership. No representative is omitted or duplicated.

Every target graph has five degree-four vertices and ten degree-one leaves.
An automorphism must map each degree class to itself, preserve the graph induced
by the five heavy vertices, and bijectively map the leaves at each heavy vertex
to the leaves at its image. Enumerating every such heavy-vertex permutation and
every leaf bijection therefore enumerates the entire automorphism group. The
checker constructs these groups from the edge lists without using the
producer's group or its canonical image catalog. A validated initial graph
isomorphism followed by this full target group covers every possible graph
isomorphism, so the orbit comparison is complete for the specified graphs.

## Dual verification

All 161 representatives were independently checked by the package verifier and
standalone checker as twenty-block pair covers on fifteen points. Each was then
mapped through the first frozen point-one fiber for its class and augmented
with point one. Both verifiers agree on twenty distinct pentads, 185 covered
triples, and 375 holes for every actual partial. Both canonical witness hashes
match. All global exact-profile residual demands are nonnegative, sum to 440,
and vanish for triples containing point one.

Full local and actual witnesses plus both verifier receipts are retained in the
ignored raw directory. The tracked representative receipt and raw index bind
each file by SHA256. Each JSON receipt is smaller than one million bytes.
Twenty-two damaged controls check malformed labels, missing and duplicate
blocks, damaged pair rows, missing and duplicate orbits, omitted settings,
incorrect old-orbit flags, invalid mappings, and both verifiers' rejection of
malformed, duplicate, or damaged witnesses. Ruff passes.

## Scope and reproduction

This audit is complete only for all extension-point choices of the four fixed
ray-target recipes. It does not enumerate all affine constructions, establish
extendability to 64 blocks, produce a full cover, or give a global exclusion.
The raw partials remain incomplete covers.

```sh
uv run python experiments/2026-10-04/affine-extension-point-variants-independent/check.py
uv run ruff check experiments/2026-10-04/affine-extension-point-variants-independent
```

Inputs and their frozen hashes are listed in `review.json`. The explicit full
groups are in `automorphisms.json`; the representative and raw indices preserve
the dual verification evidence. Re-running the checker performs finite saved
data checks only and does not call any solver.
