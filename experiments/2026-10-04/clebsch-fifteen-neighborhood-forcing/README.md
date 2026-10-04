```
Document:    Fifteen Clebsch Neighborhoods Force the Sixteenth
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      f138f8cd5bbc1b8a68183e9a2bd69896255fdfdd02f1850e7da981dc31953247
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

Within the stated Clebsch pair and triple profile, every exact 64-block cover
containing fifteen Clebsch neighborhoods must also contain the sixteenth.
The separately checked finite contradiction for all sixteen neighborhoods
therefore excludes covers in this profile containing at least fifteen such
blocks. This is a conditional construction restriction, not an unrestricted
lower bound. No optimizer or new search budget is needed for this deduction.

## Assumptions and complete candidate set

The sixteen vertices are the even-weight five-bit integers in increasing
order, labeled 1..16. Adjacency means XOR weight four. The graph has forty
edges and degree five. Require pair multiplicity six on graph edges and five
on nonedges. Require triple multiplicity one on non-P3 triples and between
one and two on P3 triples, with exactly 64 distinct pentads in total.

Fix every neighborhood N(q) except N(1). These fifteen independent pentads
cover 150 distinct independent triples. The other ten independent triples
are exactly the ten triples of N(1) = {8,12,14,15,16}. Every further pentad
must avoid the 150 covered independent triples, since their required count
is already one. Examining all 4368 pentads leaves the following complete
pool of 258, including N(1):

| Type | Count | Graph edges | Independent triples | Point 1 in block | Graph degree at point 1 |
| --- | --- | --- | --- | --- | --- |
| C5 | 192 | 5 | 0 | 60 yes, 132 no | 2 when present |
| C4 with a leaf | 30 | 5 | 1 | Always | 3 |
| P5 | 30 | 4 | 1 | Never | 0 |
| K1,4 star | 5 | 4 | 4 | Always | 4 |
| Missing N(1) | 1 | 0 | 10 | Never | 0 |

No single pair or triple row initially has insufficient support or forces a
candidate. The exact aggregate identities below give the stronger deduction.

## Exact identities

Let a,b,c,d,e count selected C5, C4-with-leaf, P5, star, and missing-neighborhood
blocks, respectively. Let x count selected C5 blocks containing point 1.
All counts are nonnegative integers, and e is zero or one.

Forty-nine further blocks are required. The graph-edge pair rows require
240 incidences, since all fixed neighborhood pentads are independent. The
ten missing independent triples must each be covered exactly once. Therefore:

```
a + b + c + d + e = 49
5a + 5b + 4c + 4d = 240
b + c + 4d + 10e = 10
```

Five edge pairs at point 1 have demand six and ten nonedge pairs have demand
five. Their total is 80, so point 1 occurs in 80/4 = 20 blocks. Exactly five
fixed neighborhoods contain point 1, leaving fifteen further occurrences.
The graph-edge pair rows at point 1 total thirty; the fixed independent
blocks contribute none. The exhaustive rooted type counts above imply:

```
x + b + d = 15
2x + 3b + 4d = 30
```

Subtract twice the first rooted identity from the second to obtain b+2d=0.
Nonnegativity gives b=d=0. Subtract the graph-edge identity from five times
the cardinality identity to get c+d+5e=5. Subtract this from the independent
triple identity to get b+3d+5e=5. Thus 5e=5 and e=1: the missing neighborhood
is forced. The aggregate solution is a=48,b=c=d=0,e=1,x=15.

## Why one omitted point is complete for this conditional case

XOR by any even-weight vertex is a permutation preserving graph adjacency,
pair types, triple types, and neighborhood blocks. XOR by the omitted point
sends it to bit pattern zero, label 1. The checker saves and verifies all
sixteen such translations. Consequently every choice of fifteen fixed
neighborhoods reduces to this case. A cover containing all sixteen already
falls under the separately checked sixteen-neighborhood contradiction.
This argument makes no reduction for covers containing fewer than fifteen
neighborhoods or having a different pair or triple profile.

## Saved finite evidence and replay

Run `uv run python experiments/2026-10-04/clebsch-fifteen-neighborhood-forcing/check.py`.
It uses standard-library arithmetic only, enumerates the full pentad pool,
checks every rooted type, verifies each coefficient identity and its unique
nonnegative integer count solution, and checks all sixteen translations.

- `candidates.json`: all 258 actual pentads, zero-based global lexicographic
  IDs, class, graph degrees, and independent-triple counts.
- `identities.json`: exact integer coefficient rows and their sole count
  solution, with the nonnegativity deduction.
- `translations.json`: all sixteen explicit permutations sending the omitted
  neighborhood point to label 1.
- `summary.json`: source and runtime pins, counts, the forcing result, scope,
  and the exact separately checked sixteen-neighborhood proof dependency.
- `files.json`: hashes of the frozen folder.

The sixteen-neighborhood dependency is
`clebsch-neighborhood-cycle-certificate/certificate.json`, SHA256
`6802e49098940c70253dbf17e0a44bc05acb800185d85356dc5031faa6c545fc`.
Its independent standard-library audit is
`clebsch-neighborhood-cycle-certificate-independent/audit.json`, SHA256
`de03e575af4237a99f5ad10083ac7f0651021c8349d3250162cef2972f752e84`.
This checker verifies both pins and the successful audit's certificate link.
The exclusion depends on that checked finite proof, not a CP-SAT status.
