```text
Document:    H9 H10 Union Prescreen and Augmentation Proposal
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      d0a491592201404c2ca02d2d1b46d52ef10bdbbcb86bf541d7513db50e66218d
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# The exact 128-block union needs at least 71 blocks

The independently checked starts a0a737 (H9/D19) and 85f6 (H10/D22) share no
blocks. Their union covers every triple, but cannot contain a 64-block cover.
Seventeen triples have exactly one union carrier, forcing 15 distinct blocks.
The producer finds 56 additional triple rows whose two-carrier supports are
pairwise disjoint and avoid all forced carriers. Each row requires a different
selected block. Therefore every cover inside this exact pool uses at least
15 + 56 = 71 blocks.

The support-size histogram is 1:17, 2:380, 3:149, and 4:14. The forced blocks
leave 413 triples uncovered. There are 303 two-carrier residual triple rows
with 249 distinct supports. The certificate's 15 singleton supports and 56
pair supports involve 127 different union columns. This is an elementary
counting bound, not a solver status or a claim about unrestricted C(16,5,3).
The true minimum within the union is not established.

The original H11 union producer and separate checker are reused with new
source hashes and recounted expected totals. The old frozen files are
unchanged. Their source hashes are respectively
`d56877e71ae9a39dc9369c07737af350096a5b40cc7e1a4274d6bf116b2559bf` and
`0790661aaa62ade51daaf35a5c814b7b81fca8fd869457347d568597d12b36f2`.
The matching algorithm is unchanged: repeatedly select the remaining edge
with smallest minimum endpoint degree, then degree sum, then full block IDs.
It need not find a maximum matching; the displayed 56 edges suffice.

`certificate.json` binds both source witnesses, all global lexicographic IDs,
the union witness, and the full 560-row incidence table. Its SHA256 is
`5a5880b2f47da5504a903f4b4f9c71d3cdc0e9c8228d047d52297dcbf29d7ecb`.
The separate checker directly recounts all carrier sets without importing
the producer. Seven damaged certificates are rejected. The package and
standalone covering verifiers agree on 9, 10, and zero holes for the two
sources and their union. The check receipt SHA256 is
`1fad82c0da1ba17189a1737f1cef4a883b0880c1b921b4b69590a955674c2009`.

No LP, covering model, native optimizer, or timed search was needed. Replay
the proof with `uv run python` on `check_certificate.py` in this folder.

# A small structured augmentation proposal

To weaken this obstruction, add columns that cover several of its 71 witness
triples at once. A direct scan of all 4,368 five-blocks finds 1,229 outside
blocks containing at least one of the sources' 19 distinct holes. Rank them
by the number q of certificate witness triples they cover, then their total
hole gain, singleton-witness gain, and lexicographic ID. The following first
eight candidates supply a compact proposed extension:

| Global ID | Block | H9 holes | H10 holes | Certificate rows q | Singleton rows |
| ---: | --- | ---: | ---: | ---: | ---: |
| 3144 | 4 5 7 10 14 | 3 | 1 | 5 | 3 |
| 3654 | 5 6 9 12 16 | 2 | 2 | 5 | 3 |
| 3560 | 4 10 14 15 16 | 0 | 3 | 5 | 2 |
| 2690 | 3 5 8 13 15 | 2 | 0 | 5 | 2 |
| 3153 | 4 5 7 12 14 | 1 | 1 | 5 | 2 |
| 3653 | 5 6 9 12 15 | 0 | 2 | 5 | 2 |
| 1860 | 2 4 11 15 16 | 0 | 1 | 5 | 1 |
| 3646 | 5 6 9 11 12 | 0 | 4 | 4 | 3 |

The IDs are zero-based positions in lexicographic combinations of labels
1 through 16. They do not change the one-based point labels.

Each old union block covers at most one of the 71 selected proof rows. If a
64-block cover uses new blocks, summing the same rows gives the necessary
condition `sum((q(new_block)-1) * selected(new_block)) >= 7`. Thus an external
block hitting five proof rows offers four units against the seven-unit gap;
one extra block from this proposed list cannot suffice. This ranking targets
the actual obstruction instead of merely adding random carriers. It is only
a proposal: the resulting 136-column pool has not been prepared, solved, or
claimed feasible. A fresh singleton/disjoint-support recount should precede
any model preparation; another short certificate could cancel it too.
