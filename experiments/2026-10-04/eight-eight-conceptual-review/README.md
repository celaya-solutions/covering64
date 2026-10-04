```text
Document:    Independent Eight Plus Eight Construction Review
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      6a0a8fd61554be673883775d130012534585ad978b81adbc2d167c33c69d3d9f
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent 8+8 construction review

The arithmetic is sound. This is a restricted construction attempt, not a safe
reduction of all 64-block coverings. No existence or impossibility result is
claimed here, and this review launches no solver.

## Construction and counts

Partition the points into two sets of eight. On each half, select eight
quadruples from its affine Steiner quadruple system SQS(8). Their 32 triples
are disjoint; the other 24 internal triples remain. Extend each selected
quadruple by one point of the other half, and each remaining triple by two
points of the other half. This gives 32 blocks per half and 64 in total.

Each half supplies `8*8 + 24*28 = 736` possible blocks, for 1,472 distinct
candidates. The 64 extension groups are disjoint: the majority half and its
internal base recover a block's group uniquely. Every selection of one block
per group covers all 112 internal triples exactly once. Sixteen blocks of
split 4+1 contribute six mixed triples each; 48 blocks of split 3+2 contribute
nine each. Thus mixed incidence is `16*6 + 48*9 = 528` against 448 required
triples. A successful cover has exactly 80 excess incidences, all mixed.
Each orientation (2+1 or 1+2) has 264 incidences against 224 required triples.

If every point lies in four selected quadruples, it lies in 12 covered
internal triples and nine remaining internal triples. It therefore belongs to
13 local base blocks. A final regular degree-20 cover would need seven
opposite-half extension incidences per point. The proposed model does not
impose final regularity; degree-19 possibilities remain allowed in the recipe.

## Why AA, AB and BB cover the stated regular-base template

Represent a half by GF(2)^3. Its 14 planes are `n dot x = b`, with seven
nonzero normals `n` and two parities `b`. An eight-plane selection that has
degree four at every point must select both or neither plane for each normal.
Indeed, the degree function is a constant plus a linear combination of the
seven distinct Walsh characters `(-1)^(n dot x)`; orthogonality forces every
nonconstant coefficient, the difference of the two selection indicators, to
be zero. Hence it selects four complete parallel classes and omits three.

An omitted triple of normals is either dependent (type A, representative
`{1,2,3}`) or a basis (type B, representative `{1,2,4}`). An invertible linear
map takes every dependent triple or basis to the corresponding representative.
Independent relabeling of the halves and exchange of the two halves leave
exactly AA, AB and BB. A separate standard-library enumeration checks all
`choose(14,8) = 3003` subsets: exactly 35 have degree four, all are unions of
parallel classes, with seven of type A and 28 of type B.

This is complete only within the degree-four selected-affine-SQS(8) base
recipe. It does not establish that an arbitrary cover has an 8+8 partition
with exact internal coverage, or that all choices of eight SQS quadruples are
regular. No such completeness condition is imposed on the global problem.

## Necessary pair-count check

For a pair within one half, let q be the number of selected quadruples through
it and x the number of opposite-half residual-triple extensions using it as
the added pair. Six internal triples contain the pair. Each selected quad
accounts for two of them, so the local base contributes `q + (6-2q) = 6-q`
blocks. Its final multiplicity is `6-q+x`, which must be at least five.
Thus `x >= max(q-1,0)`. The 24 opposite-half pair extensions imply that at
most four internal pairs can have q=0.

Type A has q histogram `{0:4, 2:24}`. It must use each q=2 pair exactly once
as an extension pair and never use a q=0 pair. The internal pair excess is
then exactly a perfect matching. Type B has histogram `{1:12, 2:12, 3:4}`;
its mandatory extension-pair load is 20, leaving four occurrences free.
These follow from covering and the recipe; they are not additional global
assumptions. They reveal no immediate arithmetic obstruction.

## Duplication check and evidence

The prior eight-pair support recipe is a different partition condition. The
prior SQS construction lifts all quadruples of two SQS(16) seeds into a fixed
1,744-block union without one-extension-per-base rules. A fresh rebuild from
its saved independent seed witnesses verifies both SQS properties and that
union. In the stored labeling, each new 1,472-block pool overlaps the earlier
union in 704 blocks and includes 768 blocks outside it. No direct duplicate
of this internal-triple recipe was found in the project notes and indexed
prior construction scripts. This is a local inventory check, not a literature
novelty claim or an exclusion of every possible relabeled pool relationship.

[check.py](check.py) is a standalone standard-library recount; it imports no
producer model helpers. [arithmetic.json](arithmetic.json) contains exact
quadruples, residual triples, pool hashes, pair histograms and old-seed hashes.
The serialized models and runtime gate are reviewed separately.
