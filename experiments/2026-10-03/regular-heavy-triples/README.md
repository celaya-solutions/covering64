```
Document:    Safe heavy-triple restrictions in the full regular branch
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      af73acb35482cb539ced654c904cf5218940afcbefc8a9797f63fc7ee71e77ac
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions```

# Full regular-cover heavy-triple restrictions

These deductions assume a full C(16,5,3) cover with exactly 64 distinct blocks and every point in exactly 20 blocks. They are not valid unchanged for partial covers with holes. They impose no incumbent or rotational assumptions.

Write lambda(p,q) for pair multiplicity and mu(p,q,r) for triple multiplicity. Each pair has lambda >=5. For each point p, sum(q !=p) lambda(p,q)=80; hence the multigraph with edge weights e(p,q)=lambda(p,q)-5 is 5-regular.

## Elementary bounds

A 20-block link of p has 120 pair incidences. Deleting point q from that link leaves 120-3lambda(p,q) incidences available to cover all 91 pairs on the other 14 points. Thus lambda<=9.

For any pair p,q, its blocks contain 3lambda(p,q) triple incidences. All 14 possible third points must occur. Fixing r therefore gives mu(p,q,r)<=3lambda(p,q)-13. Also mu<=lambda for each of its three pairs.

If mu>=6, all three pair multiplicities are at least seven, so all three pair-excess edges have weight at least two. Two such triangles cannot share a vertex: if they share an edge, a common vertex would have excess degree at least six; if they share only one vertex, it would have excess degree at least eight. Both contradict degree five. Thus all triples with mu>=6 are vertex-disjoint. Moreover mu>=8 would force two incident pair-excess weights at least three, so mu<=7.

## Exact shape forced by multiplicity seven

Let T={a,b,c} occur in seven blocks. These blocks are T plus seven distinct pairs on the other 13 points. Fourteen outside incidences force an outside point d to occur at least twice. For each a in T, the triples abd and acd then each occur at least twice. The other 12 triples through pair ad must each occur at least once. Consequently 3lambda(a,d)>=16 and lambda(a,d)>=6.

At each a, the two internal pairs already consume at least four units of its pair-excess degree five. The pair ad consumes at least one more. Equality is forced throughout: every internal pair of T has lambda=7, every pair ad has lambda=6, and all other pairs from a to outside points have lambda=5.

An internal pair occurs only in the seven T-blocks. Covering all triples through that pair forces the seven outside pairs to cover every outside point. Their degree sequence is therefore 2,1^12. Since blocks are distinct, these pairs form P3 union5K2, with the unique degree-two point d. This proves the normalized seven-block choice

```text
1 2 3 4 5
1 2 3 4 6
1 2 3 7 8
1 2 3 9 10
1 2 3 11 12
1 2 3 13 14
1 2 3 15 16
```

is existence-preserving for the regular branch having at least one multiplicity-seven triple. It is compatible with fixing the first lexicographic block. It does not cover regular designs without such a triple.

The remaining 13 blocks through each a in T avoid the other two T points. Removing a yields 13 quadruples on the outside 13 points, with every point occurring exactly four times. They must cover every pair outside the seven P3 union5K2 edges. They may also cover some or all of those seven edges; requiring their omission would be an unjustified restriction. No projective-plane uniqueness claim is made here.

## Heavy-triple count inequality

A multiplicity-seven triple consumes pair-excess degree four at each of its vertices and gives its hub d three distinct excess edges, one to each T vertex. The hub cannot belong to another multiplicity-at-least-six triple, since that would require four further excess units. It cannot be the hub of another multiplicity-seven triple, since six excess units would then be required.

If n7 counts multiplicity-seven triples and n6 counts multiplicity-six triples, the disjoint heavy triples and distinct outside hubs therefore occupy 4n7+3n6 different points. Hence

**4n7 + 3n6 <=16.**

In particular n7=3,n6=2 cannot occur in a full regular cover. A partial seed with this profile is not invalid as a partial search state; its profile must change before it becomes a full regular cover.

## Essentiality at the shared star blocks

In a shared block T union{d,u}, the three d-triples using two points of T occur in both star blocks. The other three d-triples are {a,d,u}, one for each a in T. Such a triple is private exactly when a's 13-quad family omits pair {d,u}. Each star spoke must therefore be omitted by at least one of the three local families. The independently checked finite determinant obstruction in `../thirteen-point-links/README.md` shows that one local family cannot omit both spokes. Consequently at least two local families must omit opposite spokes.

## Literature context

D. Bryant, M. Buchanan, D. Horsley, B. Maenhaut and V. Scharaschkin, **On the non-existence of pair covering designs with at least as many points as blocks**, Combinatorica (2011), [preprint](https://people.smp.uq.edu.au/DarrynBryant/Preprints/BryBucHorMaeSchNonExistPairCoverings.pdf), studies incidence-matrix and determinant restrictions for pair coverings with at most as many blocks as points. Page 2 was rendered and inspected. This is relevant methodological background, not a theorem directly applicable to the 20-block point links, which have more blocks than points, or to local families with missing pairs. The local square-Gram argument above is derived explicitly. Download SHA256: `1eb089937e67e3493c09817ca68ac18cf07314ab145d87fe21bf0309337b7007`.

J.-C. Bermond, J. Bond and D. Sotteau, **On regular packings and coverings** (1987), [public manuscript](https://inria.hal.science/hal-02508731/document), treats regular edge packings and coverings by triangles and quadruples. Its abstract was rendered and inspected. It does not supply a classification of the irregular 20-block links considered here or a different 65-block C(16,5,3) witness. Download SHA256: `c3adb4cefbc31ffc80eed39e69739e76c1472aa6e04c5bf15930f50a02857732`. Raw PDFs and page images are retained outside Git under `experiments/scratch/regular-algebra-20261003/`.
