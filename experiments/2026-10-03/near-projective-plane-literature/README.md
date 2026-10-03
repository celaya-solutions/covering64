```
Document:    Targeted Near-Projective-Plane Literature Check and Local Switches
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      2f30a668cff0d016282bdd350532cfa33ab2cc9b0415b11df158bf54a5abbcfb
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Literature finding

The four-hole and six-hole local families are **near projective planes of
order three** under the definition in Alan R. Prince, *A near projective
plane of order 6*, Innovations in Incidence Geometry 13 (2013), 97-105.
DOI: [10.2140/iig.2013.13.97](https://doi.org/10.2140/iig.2013.13.97).
The publisher's [PDF](https://msp.org/iig/2013/13-1/iig-v13-n1-p05-s.pdf)
was downloaded, text-extracted, and its first page rendered and visually
inspected. Its SHA256 is
`51768b9667163e2f0d2e76d7c4b04980fd7aa32d9f3ac789e7d8e0ae3e424ba5`.

On its first page, the paper defines a near projective plane of order n as
an incidence structure with n^2+n+1 points and lines, each point and line
having n+1 incidences, with any pair of points on at most two lines and
any pair of lines meeting in at most two points. Our three local families
satisfy this definition for n=3. A pure line meets every other line exactly
once. The paper studies an order-six construction with fifteen pure lines,
and does not supply an order-three classification or a C(16,5,3) implication.

This targeted search did **not locate** a published classification matching
our exact three-family statement, or a direct consequence for C(16,5,3).
That is a search result, not evidence of novelty or absence from the
literature. Exact Google Scholar searches for “near projective plane” with
“order 3” and “order three” returned no records in this pass. Broader searches
for near planes, symmetric 13_4 configurations, matching defects, and
incidence determinants also did not yield a directly applicable result.
Search pages and the downloaded paper remain outside Git under
`experiments/scratch/local-family-literature-20261003/`.

Related terminology needs care. A linear 13_4 configuration excludes repeated
pairs, so it cannot contain our two nonplane examples. The publisher abstract
of Blokhuis, Jungnickel and Schmidt, *On a Class of Symmetric Divisible Designs
that are Almost Projective Planes* (2001),
[DOI 10.1007/978-1-4613-0283-4_2](https://doi.org/10.1007/978-1-4613-0283-4_2),
instead describes each point as having one partner joined twice and every
other point joined once. That is a different incidence condition from our
matching-hole families. Bierbrauer, Marcugini and Pambianco, *Projective planes,
coverings and a network problem* (2003),
[DOI 10.1023/A:1024140122167](https://doi.org/10.1023/A:1024140122167), concerns
a network covering problem and designs approximating projective planes. Only
its publisher abstract and references were inspected; no theorem from it is
used here.

# Checked invariants

The following are exact calculations from the saved witnesses. The signs of
incidence determinants depend on row and column order; the magnitudes and
Gram determinants are invariant.

| Local family | Absolute incidence determinant | Gram determinant | Pure points | Pure lines |
|---|---:|---:|---:|---:|
| Projective plane | 2,916 | 8,503,056 | 13 | 13 |
| Four holes | 1,620 | 2,624,400 | 5 | 5 |
| Six holes | 1,296 | 1,679,616 | 1 | 1 |

The six-hole family's missing/repeated-pair union has two alternating cycles
of length six, corresponding to half-length partition (3,3). Its determinant
is not the other Gram-admissible six-hole value 1,260 from partition (2,4).

# Concrete local switches

The independent classification replay retained all 72 labelled projective
planes sharing the normalized four-block star at point 13. Comparing them
against each nonplane witness gives a projective plane sharing nine blocks
with the four-hole family and seven blocks with the six-hole family. Thus
class changes can be performed by replacing four or six quadruples instead
of all thirteen. These are maximum overlaps within those 72 normalized
planes; no global nearest-projective-plane claim is made.

`pg-trades.json` records each exact nearest plane, its point map from the
canonical saved projective-plane witness, the common blocks, and both sides
of the switch. Every point map was directly applied to all thirteen blocks
and checked. `analyze_families.py` reproduces the invariants using rational
Gaussian elimination and the point maps using NetworkX incidence-graph
isomorphism. The labels in this file are the source-local labels 1..13.

For a current mapped nonplane family, apply its current point map to the
stored nearest-plane blocks to obtain a four- or six-block switch to a plane.
In the reverse direction, compose the current plane embedding with the inverse
of the stored canonical-plane-to-nearest-plane map. Then apply that map to
the saved target nonplane blocks. A search must still verify that the new
missing pairs lie within its chosen G and preserve any required omitted
spoke. A class switch can change coverage of outside triples and is a search
move, not a proof that a global completion exists.

```sh
uv run --with networkx==3.7 python experiments/2026-10-03/near-projective-plane-literature/analyze_families.py
```
