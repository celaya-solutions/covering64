```
Document:    Independent Classification of Normalized Nineteen-Block Links
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      1fb8d53c241dadd1621e01410a8f7f0b80e0775ddeedeb59715d2d28663859d1
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent classification of normalized nineteen-block links

This audit assumes the previously derived normalization: the repeated-pair graph is a four-leaf star plus five disjoint edges. It does not prove a lower bound for C(16,5,3).

The hub occurs in six blocks. Each star leaf occurs in two of those blocks, and each of the other ten points occurs in one. Representing the six blocks as vertices gives four simple leaf edges A and five matching-pair edges B. B may have loops, each using two slots. Every vertex has total degree three. Parallel A edges are forbidden because they would repeat a leaf pair. Reordering hub blocks acts by S6; relabeling leaves and matching pairs removes all edge labels. Thus classifying A under S6 and B under Aut(A) loses no normalized hub configuration.

An independent integer-matrix enumeration found 1,335 labeled A graphs, eight A classes, and 206 colored hub classes. The list exactly matches the builder. A separate exact residual-decomposition DFS exhausted all 206 cases in 31,989 nodes, with no timeout. A third implementation replayed every tree using dictionaries and sets.

| Hub shape | Distinct labeled links | Hub automorphisms | Link classes |
|---|---:|---:|---:|
| 1 | 12 | 48 | 1 |
| 4 | 4 | 8 | 1 |
| 44 | 2 | 4 | 1 |
| 47 | 96 | 384 | 1 |

The other 202 hub shapes have no residual decomposition. The 114 links exactly match the independently compared CP solution sets. All 114 passed both the package verifier and standalone checker as C(15,4,2), after shifting labels 2..16 to 1..15. Their prescribed pair multiplicities were also checked directly.

Every full-link isomorphism preserves its repeated-pair graph. That graph has exactly 4! times 5! times 2^5 = 92,160 automorphisms. The primary classifier filters these to maps preserving the six hub blocks. The independent audit instead permutes the six hub blocks, forces leaf images, and enumerates matching-edge permutations and loop endpoint swaps. It reproduces the four subgroup sizes above, validates every canonical assignment, and finds no hub map for any of the six cross-shape comparisons. Therefore the 114 normalized links represent four isomorphism classes, conditional on the stated excess-graph normalization.

Thirty focused controls pass. They include omitted classes, parallel leaf edges, loop degree accounting, malformed labels, duplicate links, omitted proof branches, false solution leaves, damaged state counts, and budget-limited UNKNOWN. Hashes are repaired in proof-damage controls so rejection tests the mathematics rather than only integrity checks.

## Saved evidence

- `experiments/2026-10-03/link-hub-independent/` contains the shape audit, isomorphism audit, source hashes, witness checks, comparison data, all 114 small witnesses, and the decomposition manifest.
- Full per-case trees remain outside Git in `experiments/scratch/link-hub-independent-dfs-20261003/` (about 1.04 MB). Their hashes are preserved in the committed-size manifest.
- `scripts/audit_link_hub_shapes.py` independently classifies hub shapes using integer matrices.
- `scripts/enumerate_link_hubs_independent.py` produces exact decomposition trees without CP or package imports.
- `scripts/check_link_hub_trees.py` replays complete trees without importing the producer.
- `scripts/audit_link_isomorphism.py` independently checks the link isomorphism classes through hub-block permutations.

The exhaustive statements concern normalized nineteen-block links. They do not settle whether any of the four link classes extends to a 64-block cover, and they do not address the all-points-degree-twenty branch.
