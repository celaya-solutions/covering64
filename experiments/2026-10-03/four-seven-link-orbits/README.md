```
Document:    Independent First Heavy-Link Orbit Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      5a014b00cb1f74b5e51abc5a08bd20b5baad573d12faa54d4653a6ffd691cd61
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent audit of the first-heavy-link label quotient

The audit passes for both normalized hub cases. Each case has exactly 29,970
labeled first-heavy links and 129 orbits under a group of order 432. All 59,940
saved maps across the two cases were independently checked in both directions.

A first-heavy link has seven distinct outside pairs on points 4 through 16.
Point 4 has degree two; every other point has degree one. No edge joins two
anchors in any of (5,6,7), (9,10,11), or (13,14,15). Select point 4's two leaves
and a perfect matching on the other ten points. Before excluding forbidden
edges there are `C(12,2)*9!! = 62,370` such links.

Inclusion-exclusion over the three forbidden anchor triangles gives

`sum(j=0..3) (-1)^j C(3,j) 3^j C(12-2j,2) (9-2j)!!`
`= 62,370 - 42,525 + 11,340 - 1,215 = 29,970`.

A disjoint set of forbidden matching edges contains at most one edge from each
anchor triangle. The independent checker generates every unfiltered matching,
then excludes forbidden edges and validates every resulting link.

The group fixes points 1,2,3,4 individually. It independently permutes the three
anchors within each outer group, and applies the weighted hub-graph stabilizer
of group zero. Exhaustion of all 24 group permutations leaves two: the identity
and a swap of groups 1 and 3 for the cycle, or groups 2 and 3 for the matching
(using zero-based group indices). Thus the group order is `6^3*2=432`.
The checker explicitly reconstructs all permutations, verifies every inverse and
every product, and checks preservation of all 120 pair targets and anchor groups.

The independent full-group images of the representatives are disjoint, cover all
29,970 links, have the claimed sizes, and use their lexicographic minima. Both
cases have this orbit-size histogram:

| Orbit size | Number of orbits |
| --- | --- |
| 18 | 1 |
| 36 | 5 |
| 54 | 2 |
| 72 | 4 |
| 108 | 20 |
| 216 | 68 |
| 432 | 29 |

The archive stores `from_representative` maps (representative to member), not
member-to-representative maps. The checker verifies those maps and their inverses.
It rejects eight damaged controls per case: repeated endpoint, a permutation
moving the first group, a missing family, a duplicate family, a missing orbit,
a valid permutation with the wrong image, a wrong family count, and a wrong
orbit-size histogram.

This is a safe label quotient in the regular four-sevenfold branch. Relabeling
any cover and its first link by a permitted permutation preserves coverage,
cardinality, point degrees, heavy groups, and pair labels. It therefore reaches
one of the listed representatives. No cover is required to be invariant under
any nonidentity permutation. The classification neither produces a cover nor
rules out any of the 129 branches.

Evidence:

- `source.py`: frozen production enumeration source.
- `result.json`: original results and hashes; its original audit-pending field is
  retained for provenance. The independent result below supersedes that field.
- `relabelings.json.gz`: every explicit representative-to-member map.
- `independent_check.py`: standard-library-only audit; imports no production code.
- `independent-result.json` and `independent-run.log`: audit evidence.

The map archive SHA256 is
`3ea74028d4cb7c5bac4b48121acee05802c85f2ff5c417fecab8b0036cdb3dda`.
The checker source SHA256 is
`42f3ea836dca8d74ab841c4e99632cc3ea88c1bc41cdfe7a16726bbd06a7a682`.

Reproduce from the repository root:

```sh
uv run python experiments/2026-10-03/four-seven-link-orbits/independent_check.py
```

The header hash is over this body, including its initial blank line. The Python
checker's header hash similarly includes the separator blank line after its
nine comment lines. Reported source hashes are whole-file hashes.
