```
Document:    Complete First-Family Cases for a Point-Essential Heavy Triple
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      12520ff4e7c42e918e474f805ad88d9e767d7790928b5f70a045c9bdb226dc2e
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Result and scope

There are **13 first-family cases** for the normalized, point-essential
triple-of-multiplicity-seven branch: nine cases from the four-hole local family
and four cases from the six-hole local family. The complete local-family
classification is in `../local-family-classification/`; its independent root
audit is in `../local-family-root-audit/`.

These are exhaustive seeds for that branch, not completed C(16,5,3) coverings.
This first-family reduction uses point-essentiality at the hub in the shared
star blocks. It does not by itself justify assuming point-essentiality for an
arbitrary regular covering. Any reduction establishing that assumption must
be supplied separately.

The outside points are **4 through 16**. The fixed graph G consists of the
spokes {4,5}, {4,6}, and the independent edges {7,8}, {9,10}, {11,12},
{13,14}, {15,16}. The first local family omits **{4,5}**. Every representative
in `first-families.json` contains its thirteen quadruples on these labels, its
map from the classified source witness, and the full twenty blocks obtained
by adjoining point 1 to those quadruples and including the common seven blocks:

```text
1 2 3 4 5
1 2 3 4 6
1 2 3 7 8
1 2 3 9 10
1 2 3 11 12
1 2 3 13 14
1 2 3 15 16
```

# Completeness argument

Point-essentiality at point 4 of block {1,2,3,4,5} requires at least one of
{1,4,5}, {2,4,5}, {3,4,5} to be private. The other triples in that block
through 4 occur in both shared star blocks. Consequently at least one of the
three local families omits {4,5}. Permuting the three points {1,2,3} places
such a family first. The projective-plane local family omits no pair, so the
first family belongs to the four-hole or six-hole class.

For a source family with r missing pairs, choose r-1 of the five independent
G edges and include the fixed spoke {4,5}. These are all possible target hole
matchings: {4,6} cannot join a matching already containing {4,5}. Enumerate
every bijection from the source hole edges to the target edges, both endpoint
orientations for each edge, and every bijection between the remaining source
and target points. This includes every admissible point relabeling. Equal
block sets are removed by exact comparison, independently of automorphism
group calculations.

The resulting complete counts are:

| Source class | Point maps tested | Distinct labelled families |
|---|---:|---:|
| Four holes | 10 x 4! x 2^4 x 5! = 460,800 | 28,800 |
| Six holes | 6! x 2^6 = 46,080 | 15,360 |

The stabilizer in Aut(G) of the omitted spoke fixes points 4,5,6 individually.
It permutes the five independent edges and independently swaps their endpoints.
The script explicitly constructs all 5! x 2^5 = **3,840** such point maps and
checks that each preserves G. Their action partitions the labelled families.
For each unprocessed family, applying every group element produces its full
orbit. Every image is checked against the exhaustive family pool. Orbits are
disjoint, their union is the entire pool, and orbit size times stabilizer order
is checked to equal 3,840. No graph-isomorphism library is used for this quotient.

The four-hole pool has six orbits of size 3,840 and three orbits of size 1,920:
nine cases. The six-hole pool has four orbits of size 3,840: four cases. Every
point map can be extended to all sixteen points by fixing 1,2,3; it therefore
preserves the common seven blocks. This is a safe normalization of the first
family and imposes no restriction on the eventual second and third families.

# Checks and retained evidence

Every one of the 44,160 distinct labelled families is checked to have the
specified number of holes, all within G and including {4,5}. For every family
the archive records a source-witness-to-family bijection and a
family-to-representative bijection. Both maps are applied directly to the
thirteen blocks and checked. All indices and labels are one-based in the
archive; block IDs follow lexicographic quadruple ordering on points 4..16.

Each representative's twenty blocks through point 1 give a full C(15,4,2)
point link. Removing point 1 and relabeling points 2..16 as 1..15 produces the
saved `r4-...-point-link.txt` and `r6-...-point-link.txt` witnesses. Both the
package verifier and the separate standalone checker accept all thirteen
links as full pair coverings with twenty distinct quadruples. These are
local point-link checks, not verification of a full sixteen-point covering.

The larger compressed map archive stays outside Git under
`experiments/scratch/first-family-orbits-20261003/`. Its path, size, SHA256,
and record count are recorded in `first-families.json`. The script is
deterministic, uses no random seed, and records its 120-second budget, source
revision, source hash, Python version, and elapsed time. A timeout raises an
error instead of writing a completed quotient report.

```sh
uv run python experiments/2026-10-03/local-template-orbits/enumerate_first.py --seconds 120
```

For comparison, `pg-automorphisms.json` records a live incidence-graph
automorphism calculation for the projective-plane family. The six nauty
generators produce exactly 5,616 distinct point permutations, and every one
was directly checked on all thirteen blocks. Thus there are 13!/5,616 =
1,108,800 point-labelled projective-plane families. This count is not used
by the first-family quotient.
