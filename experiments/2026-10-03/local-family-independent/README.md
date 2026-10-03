```
Document:    Independent Review of the Local Family Classification
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      aac54ce7aa9ec97722ce280f76dabc340cb23b326d56bb5c7dd81c421e46a49c
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Scope

The reviewed classification concerns 13 distinct quadruples on 13 points, each point in four blocks, with a matching as the missing-pair graph. Its use for a multiplicity-seven triple in a full regular covering additionally needs the separate no-both-spokes result. This audit does not duplicate the direct C++ enumeration or claim a global covering-number result.

# Completeness review

At a point, the 12 pair incidences equal the number of other points. Thus missing-pair degree equals positive pair excess. A missing matching forces the excess graph to be a disjoint matching on the same endpoints; no pair can have multiplicity three. There is a point outside the matching. Its four incident blocks partition the other twelve points into four triples, since every pair through it occurs once. Relabeling that point to 13 and its four triples to the stated groups preserves an instance from every isomorphism class.

Every missing edge joins two different groups. A vector recording the six cross-group edge counts has degree at most three at each group. Every such vector is realizable. For a fixed vector, all endpoint placements differ by permutations inside the groups, because a matching never reuses an endpoint. Permuting groups accounts for the remaining symmetry. An independent Burnside calculation gives counts `1,1,3,6,7,5,3`, totaling 26. No incidence or rotational assumption enters this normalization.

The Python Gram filter is necessary: its 13 by 13 matrix is the incidence matrix times its transpose, so its determinant is an integer square. Fraction Gaussian elimination independently reproduced all eleven determinant values and square decisions. The colored graph quotient preserves the four-group partition and distinguishes missing edges from repeated edges. Thus a quotient step identifies equivalent pair requirements and cannot remove a non-equivalent completion.

The exact residual decomposition branches on a positive pair demand and enumerates every needed subset of legal unused blocks through it. Every completion contains one such subset. Nonnegative residual capacities and exact consumption preserve completeness. The direct C++ version instead branches on an uncovered nonmissing pair, trying every currently legal block. Degree and excess caps are necessary and monotone. If all nonmissing pairs are already covered before nine blocks, any further quadruple would add three excess incidences at each of its points, exceeding the bound of at most one. Its early return is therefore safe. Inspection found no omitted completion case in either branching argument.

# Independent symmetry and map counts

A standard-library backtracking search enumerated every point bijection preserving the four-hole family. It uses pair multiplicities and partial block images only as necessary pruning conditions, then checks every complete image against the whole block set. It found 16 automorphisms in 258 search nodes. All four missing edges form one orbit. The unmatched points have orbits `{1,2,3,13}` and `{4}`; the image of point 4 must not be silently fixed when generating embeddings.

A four-edge matching inside `P3 + 5K2` has 25 possible images: five use no spoke and twenty use one spoke. For each image there are `4! * 2^4 * 5!` point bijections. Every resulting labeled family has exactly 16 preimages, one for each source automorphism. Therefore there are exactly 72,000 distinct embedded four-hole families: 14,400 without a missing spoke and 57,600 with one missing spoke. This is an embedding count for this isomorphism class, not a claim that any three such families complete to a covering.

The six-hole representative has automorphism order three, independently found in 59 nodes. Its complete embedding count is `2 * 6! * 2^6 / 3 = 30,720`, consistent with the audited two-orbit pool. As a cross-check on the four-hole counts, the two normalized missing-graph types represent 1,296 and 972 actual matchings. Their six and two completions give 9,720 normalized families, equal to the orbit mass computed from the automorphism order and five choices of an unmatched normalization point.

The compact source and exact result are `audit.py` and `result.json`. They preserve input, proof, replay-source, and audit hashes. The separate classification archive supplies the exhaustive direct replay, independent family checks, and damage controls.
