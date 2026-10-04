```
Document:    Partial-Start Structural Diagnostics
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      7c3e1bac2fb16a1a2c7c6b570ac88e1ee747a85a711554527bbf932ce3b7f553
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Partial-start structural comparison

This read-only diagnostic compares two saved families with 64 distinct blocks. Both pass the package and standalone structural checks, and both are noncovers. All point labels and block-variable IDs retain their original 1-based point and lexicographic block conventions.

| Measure | H9 | H12 |
|---|---:|---:|
| Uncovered triples | 9 | 12 |
| Point multiplicity histogram | 19:5, 20:7, 21:3, 22:1 | 19:5, 20:6, 21:5 |
| Pair multiplicity histogram | 4:4, 5:77, 6:34, 7:5 | 5:83, 6:34, 7:3 |
| Single-triple deficit: sum of pair maxima | 8 | 0 |
| Single-triple deficit: full row sum (D3) | 104 | 0 |
| Quadruple deficit: sum of pair maxima | 8 | 0 |
| Quadruple deficit: full row sum (D4) | 96 | 0 |
| Two-triple deficit: sum of pair maxima (D2max) | 23 | 34 |
| Two-triple deficit: full row sum (D2sum) | 639 | 34 |
| Two-triple violated rows / pairs | 375 / 19 | 34 / 34 |
| Four named core overlaps, in pilot order | 1, 0, 0, 0 | 1, 1, 1, 2 |

Histogram entries mean `multiplicity:number of points or pairs`. H9 has fewer holes and a smaller sum of pair maxima, but larger total deficits and four pairs of multiplicity four. H12 has no single-triple or quadruple deficits; its 34 violated two-triple rows each have deficit one. These profiles support comparing two different partial starts. They do not prescribe new constraints or predict which start will search better.

For a pair P, point x outside P, and distinct points x,y outside P, the positive-part row deficits are:

- Single-triple: `max(0, 13 - 3*c(P) + c(P union {x}))`.
- Quadruple: `max(0, 12 - 3*c(P) + 2*c(P union {x,y}))`.
- Two-triple: `max(0, 12 - 3*c(P) + c(P union {x}) + c(P union {y}))`.

The checker enumerates all 1,680 single-triple rows and each set of 10,920 quadruple and two-triple rows. It separately sums every row and the maximum within each of the 120 pairs. Counts are checked by direct block containment as well as subset enumeration. It verifies incidence totals and the top-two identity, binds both prior all-relabel certificates and the four-core manifest, and saves both verifier receipts. No optimizer is called.

Candidate SHA256 values:

- H9: `15db6bdbf8c6210c6754cbe52a1408dda6a279429bb5471cf03a1b68b24f0c46`.
- H12: `330788e4a6f24e1852b047f5cd2447bfa83da66ea8c6daba3287eb53088c4b00`.

`diagnostic.json` contains all point counts, pair details, uncovered triples, exact paths, hashes, and verifier receipts. The all-relabel certificates are prior bound inputs; this diagnostic does not rerun or alter them. It supplies no global existence or lower-bound conclusion for C(16,5,3).
