```text
Document:    Public Covering Records and Two Additional Search Seeds
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      f21e51eab1e8038e151d066f627b5c192e4bfa80e97dc15acdcdae51a1de8f9c
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

## Result and scope

The public record was refreshed on 2026-10-03 at about 18:03 UTC. The [current history](https://coveringrepository.com/history.aspx?id=110841) still records **61 <= C(16,5,3) <= 65**, with the 65-block cover attributed to Rade Belic on 06/08/1997. No 64-block public witness was found. Saved browser evidence is `target-table.json`. This is evidence about the checked table, not an exhaustive novelty claim or a proof that 64 is impossible.

This continuation found two verified 65-block seeds by taking point links of a larger published cover. Their different incidence counts prove that neither full cover is a relabeling of the baseline, and that they are not relabelings of each other. However, an explicit check then proved that their rigid 60-block cores are both isomorphic to the baseline's core. They therefore do **not** provide new rigid-core search basins or improve the bound. They are derived from an already public construction and are not claimed as previously unknown designs.

## Larger source and derived seeds

The [C(17,6,4) table entry](https://coveringrepository.com/systems.aspx?v=17&k=6&t=4&m=4), checked at about 18:05 UTC, records lower bound 173 and upper bound 188, attributed to Bluskov and Hamalainen, method "JCD 1998, pp. 21-41", dated 30/04/1999. Snapshot: `larger-table.json`. The [free block-list download](https://coveringrepository.com/download_system.aspx?id=121553) was retrieved at 18:05:42 UTC and saved as `source-17-6-4-188.txt`.

Raw source SHA256: `9b702468ba6e302bc73850fd10691b78416af241e14ba28ecb4e0cbdd39f8b12`.

Independent enumeration checked 188 distinct valid 6-subsets of 1..17 and all 2,380 4-subsets covered. Points 2 and 9 each occur in exactly 65 blocks; no point occurs fewer than 65 times. For each point, retain its incident blocks, remove the point, and relabel the remaining points increasingly to 1..16. Every triple is covered because its union with the removed point was a covered 4-subset. `derive_links.py` reproduces both block lists and `derived-links.json` from the saved source.

| Seed | SHA256 | Sorted point-degree histogram | Pair-degree histogram |
| --- | --- | --- | --- |
| Existing Belic baseline | See baseline provenance | 20 occurs 12 times; 21 occurs 3 times; 22 occurs once | 5:88; 6:14; 7:18 |
| `link-at-2-65.txt` | `5c5d369e3ccc4dc7e96414d2c76da7622983da08cfb3dd1c0a2dc4a7af37fb41` | 20 occurs 11 times; 21 occurs 5 times | 5:86; 6:18; 7:16 |
| `link-at-9-65.txt` | `99d6ae99dba4a121797a23f3fcf14e6572542b5559f994a5f370a7ce67e2f028` | 20 occurs 11 times; 21 occurs 5 times | 5:85; 6:20; 7:15 |

Both seeds pass `uv run covering64 verify ... --expected-blocks 65` and the standalone `uv run python scripts/check_cover.py ... --expected-blocks 65`, covering all 560 triples with 65 distinct blocks. The four outputs are saved as `link-at-{2,9}-{package,independent}.json`. These invariant differences prove nonisomorphism of the full covers; matching invariants alone would not prove isomorphism. They do not imply a different underlying search basin.

## A checkable obstruction for this fixed core

`fixed-core-certificate.json` lists the exact 60 baseline blocks, their 15 uncovered triples, every possible completion choice, hashes, and two core relabelings. The standalone standard-library checker `check_fixed_core.py` reconstructs these values and checks exact equality against the saved certificate. It uses no project model, CP-SAT, or external graph library. Run it from any working directory; the default paths refer to this evidence folder. The `--write` option regenerates the certificate. It rejects Python's assertion-disabled `-O` mode.

The 60-block core is defined by removing the five blocks whose private triples use only four labels. In baseline labels, the five four-point supports are:

```text
1 3 6 7
2 7 14 15
4 7 8 10
5 7 13 16
7 9 11 12
```

They share point 7. Removing that point gives five disjoint three-point groups covering the other 15 points. The core covers 545 triples. Its missing triples are exactly point 7 together with each of the three pairs in each group: 5*3=15 missing triples.

Every block without point 7 covers none of these missing triples. A block with point 7 has four other points. If it takes `n_i` points from group i, its residual gain is `sum binomial(n_i,2)`, where `sum n_i=4` and every `n_i<=3`. The maximum is 3, attained exactly by distribution (3,1,0,0,0). The checker separately enumerates all 4,368 possible 5-blocks, finding gain histogram `{0:3408, 1:810, 2:90, 3:60}`.

Consequently, any cover **retaining these exact 60 core blocks** needs at least ceil(15/3)=5 further blocks, hence at least 65 total. This is a rigorous restricted obstruction, not nonexistence of an unrestricted 64-block cover. To search for 64, at least one core block must change.

Each optimal fifth block consists of one four-point support plus any one of the remaining 12 labels. The five sets of choices are disjoint, and all five supports must be represented to cover their disjoint residual triples. Thus the fixed-core 65-block completion family has exactly `12^5 = 248832` covers. The checker verifies every support's 12 choices and residual coverage; the product count follows from their independence.

Explicit point images, baseline labels 1 through 16 in order, prove that both derived cores belong to this same family up to relabeling:

```text
To link-at-2: 1 2 12 14 3 5 16 8 11 4 10 6 15 9 7 13
To link-at-9: 1 2 10 13 4 9 16 7 12 8 15 3 11 14 5 6
```

The checker confirms each image is a permutation and that the relabeled baseline core equals the corresponding 60-block core as an exact set. The maps were initially found with graph isomorphism, but verification needs only the saved permutations. This restricted obstruction is a local derivation from the witnessed block lists, not a newly located published theorem.

## Certified symmetries and removal representatives

`core_automorphisms.py` uses a colored point-block incidence graph to find automorphisms. It finished in approximately 18 seconds using NetworkX 3.7 and SymPy 1.14.0, reporting 60 graph automorphisms and exhaustion. It saved three generators in `core-automorphisms.json`. Each is recorded as the images of labels 1..16, and each was directly checked to preserve the exact core blocks.

The separate standard-library checker `check_core_automorphisms.py` does not trust graph-isomorphism completeness. It closes those three permutations under composition, obtains exactly 60 permutations, verifies all 60 preserve the core, and computes their induced permutations on the 60 lexicographically sorted core blocks. Its output `core-removal-orbits.json` contains every group element and a partition of all one-, two-, and three-block removal sets:

| Removed core blocks | All removal sets | Orbits under the certified subgroup |
| ---: | ---: | ---: |
| 1 | 60 | 3 |
| 2 | 1,770 | 40 |
| 3 | 34,220 | 619 |

The representatives and induced block permutations use **1-based indices into the explicitly listed, lexicographically sorted `core_blocks`**. The checker verifies that all removal sets occur in exactly one listed orbit and that the sizes sum to the correct total. Run `check_fixed_core.py` followed by `check_core_automorphisms.py` to anchor the subgroup to the original baseline. The second check also compares the regenerated data against the saved certificate; `--write` regenerates it. Only the verified subgroup is needed to transfer a restricted removal-case result to its orbit. No claim about arbitrary covers follows from these symmetries.

Removal-orbit certificate SHA256: `71ceb6e8a84097d850e901851a183de5a01f9a9d5044adfcfbef0277ca405ab9`.

## Another induced-construction source

The [C(17,5,3) entry](https://coveringrepository.com/systems.aspx?v=17&k=5&t=3&m=3), checked at about 18:08 UTC, records exactly 68, attributed to Jan de Heer, cyclic symmetry, dated 28/03/2001. Snapshot: `cyclic-table.json`. The [free download](https://coveringrepository.com/download_system.aspx?id=108634) was retrieved at 18:08:13 UTC, saved as `source-17-5-3-68.txt`, SHA256 `7d3232d0c7eb011c1907232374b0b0d581440dc5dd327b998233e89c87ccc841`.

Independent enumeration checked 68 distinct valid 5-subsets and all 680 triples on 17 points; every point occurs 20 times. Removing point 17 leaves 48 unchanged 5-blocks and 20 residual 4-blocks. A suggested restricted search uses the 48 unchanged blocks and all 12 extensions of each residual 4-block to size 5 on the remaining 16 points, then minimizes a cover of all 560 triples over that candidate pool. This suggestion was passed to the exact-search agent; this report claims no solver outcome. A failure in that pool would not be global.

The construction is supported by Gordon, Kuperberg and Patashnik, [*New constructions for covering designs*](https://arxiv.org/abs/math/9502238), 1995, sections 4 and 6.1. Section 4 describes intersecting existing blocks with a smaller ground set, extending undersized blocks and covering oversized blocks with smaller local coverings. Section 6.1 describes taking a point link. The [PDF](https://arxiv.org/pdf/math/9502238) was read at about 18:04 UTC; SHA256 `4d829850a3fbd6b6e827afe1ab9eefdbff6ffa9ea228b326dae202812610f3a9`. PDF and extracted text remain outside Git in `/tmp/covering64-web-resume-1803`.

## Published lower-bound check and a safe case split

Horsley and Singh, [*New lower bounds for t-coverings*](https://arxiv.org/abs/1706.06825v2), 2017, was read at about 18:21 UTC. [PDF](https://arxiv.org/pdf/1706.06825v2), SHA256 `1477ecaa5a21950b92ea9c2f3a0d7a60f97867c721af47e5108b3009b135a31d`, remains outside Git. Equation (1) states the general link lower bound `b(X) >= C(v-|X|, k-|X|, t-|X|)`. For this target, their Theorem 6 with s=1, b1=19 and b2=5 has a1=14 and d=1 and gives only ceil(16*20/6)=54, weaker than 61. Theorems 15 and 18 require b_s < binomial(k,s), which fails here because 19 is not less than 5. The paper's table of improvements for t=3 has no k=5 entry. This source does not exclude 64 blocks.

An additional complete case split follows from elementary counting, not a new theorem claimed from that paper. In a 64-block cover, every point occurs at least 19 times and the sum of the 16 point counts is 320. Either every count is 20, or some count is 19. In the latter case, relabel a point of count 19 as point 1. Its link is a 19-block (15,4,2) cover. Every link point occurs at least five times, and their counts sum to 76; therefore exactly one occurs six times and all others five times. Relabel the exceptional point as 2.

The pair-excess multigraph of this link assigns an edge multiplicity equal to the number of link blocks containing the pair, minus one. Its vertex degrees are `3*link_degree - 14`, hence degree four at point 2 and degree one at each of the other 14 points. Parallel edges are impossible, so the graph consists of a four-edge star and five disjoint edges. We may relabel its star neighbors as 3,4,5,6 and its remaining edges as (7,8), (9,10), (11,12), (13,14), (15,16). Thus every triple containing point 1 has multiplicity two for these nine pairs and multiplicity one for all other pairs. The all-counts-20 branch together with this canonical count-19 branch preserves existence. It fixes an excess pattern, not a specific incumbent link. It must not be combined with incompatible degree ordering or first-block normalization without another completeness argument.

## Independent review of the regular-action experiment

The explicitly listed regular-action generator and strict four-orbit enumerator were reviewed read-only at about 18:20 UTC. The reviewer independently reconstructed the generated groups from the 17 saved sets of point permutations, checked regularity, recomputed lexicographic representatives of all block and triple orbits, and regenerated every saved 273-entry mask list. All 17 lists and recorded hashes matched. Each action had 273 block orbits and 35 triple orbits of size 16. Each saved exhaustive log reported binomial(273,4)=226,387,980 combinations. The C++ parser now rejects invalid tokens, extra entries, negative values and values outside 35 bits.

No soundness problem was found for the stated scope, namely unions of four orbits under these explicit actions. The 17 actions are not asserted to represent 17 distinct abstract groups or to exhaust all groups. The outer result states this limitation correctly. The inner C++ log's `translation_invariant` wording means group translations in this use and should not be mistaken for a claim limited to the elementary abelian group or for an unrestricted theorem.

## Novelty and remaining limits

A valid cover with at most 64 distinct 5-blocks would improve the upper bound in the inspected current repository. It would still need a wider prior-art check before any claim of historical discovery. A new labeling or a new 65-block isomorphism class does not meet the requested target. Search-engine results did not provide a 64-block witness. No external contact or publication occurred. File hashes and recording metadata are collected in `manifest.json`.
