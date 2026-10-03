```
Document:    Published classification and alternative construction evidence
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      06b3a5aaa9402081a9ef6a584bdacdfa028c63606bed153f9b70ec98feb882ab
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Published classification and construction checks

The classification of optimal 19-block C(15,4,2) coverings was already published. This work recovered the result and matched all four published examples to the independently enumerated local classes. It makes no new classification claim and gives no 64-block witness or global lower bound for C(16,5,3).

## Primary classification

J. L. Allston, R. W. Buskens and R. G. Stanton, **An Examination of The Non-Isomorphic Solutions to A Problem in Covering Designs on Fifteen Points**, Journal of Combinatorial Mathematics and Combinatorial Computing 4 (1988), 189–206. [Publisher page](https://combinatorialpress.com/jcmcc-articles/volume-004/an-examination-of-the-non-isomorphic-solutions-to-a-problem-in-covering-designs-on-fifteen-points/) · [PDF](https://combinatorialpress.com/article/jcmcc/Volume%2004/vol-004-paper%2015.pdf).

**Theorem 12, printed page 204 (PDF page 16):** there are four distinct (2,4,15) covering designs. Two, B3 and B4, extend a D(2,3,10) packing; D1 and D2 do not. The notation describes pair coverings by quadruples. Printed page 190 states that there are 19 quadruples and proves the replication pattern 6,5^14. Relevant page images were inspected, rather than relying on OCR alone.

The four block lists were manually transcribed from printed pages 195,196,199. D1/D2 use the shared blocks and column convention on pages 197–198. Each numeric witness passed both the package verifier and scripts/check_cover.py with v=15,k=4,t=2,expected=19. All maps were checked by applying them directly to every block.

| Published design | Local hub shape | Printed block-list page | Automorphism order reported in paper |
| --- | ---: | ---: | ---: |
| B3 | 47 | 195 | 4 |
| B4 | 44 | 196 | 2 |
| D1 | 4 | 199 | 2 |
| D2 | 1 | 199 | 4 |

Numeric witnesses and `published-four-class-mappings.json` are retained here. The JSON includes the original symbols, conversion to 1-based labels, package and standalone verification, point maps and target hashes. Raw transcription script, page renders, OCR, downloaded PDF and publisher snapshots remain under `experiments/scratch/structural-novelty-20261003/`. The mapping run used NetworkX 3.7; isomorphism output was checked directly afterward.

PDF SHA256: `dd229074b271c22475bae2993daa9cf089a988f3670237c742e22246dcb93e8d`.

## Published 65-block construction

Iliya Bluskov's thesis **New Designs and Coverings**, Corollary 2.3.18, printed page 39 (PDF page 47), states C(16,5,3) <=65. Theorem 2.3.17 begins with the unique Steiner 3-(17,5,1) design and constructs a mixed cover with 168 six-blocks and 20 five-blocks. Point 17 occurs in 68 blocks; every other point occurs in 65. Point links yield the bound. The relevant corollary page was rendered and inspected. This construction does not classify all 65-block covers.

[Thesis PDF](https://www.collectionscanada.ca/obj/s4/f2/dsk3/ftp04/nq24295.pdf). Related journal article: I. Bluskov and H. Hämäläinen, **New upper bounds on the minimum size of covering designs**, Journal of Combinatorial Designs 6(1),21–41 (1998), DOI `10.1002/(SICI)1520-6610(1998)6:1<21::AID-JCD2>3.0.CO;2-Y`.

Daniel Gordon's [Coverings handbook chapter](https://dmgordon.org/papers/hcd.pdf), Theorem 1.25 and Table 1.42, independently corroborates C(15,4,2)=19 and the excess graph K1,4 union5K2. It was not used as a source for the four-class count.

## Alternative 65-block construction search

The published C(18,7,5)=548 cover attributed to Jan de Heer and Steve Muir, dated05/03/2007 on [CoveringRepository](https://coveringrepository.com/systems.aspx?v=18&k=7&t=5&m=5), was downloaded and double-verified. Exactly22 point-pair links have65 blocks. Each link was double-verified. Every one has five flexible blocks and a60-block rigid core isomorphic to the Belic core; every isomorphism was checked directly on all60 blocks. This source yielded no new rigid core. Details, derived witnesses and point maps are in raw `links18/report.json` and `links18/core-isomorphisms.json`.

A separate target65 search in the288-block pool induced by deleting point17 from the published C(17,5,3)=68 cover returned UNKNOWN after120.000896 seconds with seed2026100327. It found no witness and establishes no nonexistence result. Raw model, source snapshot, metadata and log are in `experiments/scratch/structural-novelty-20261003/induced65/`.

`sources.json` records source URLs and hashes. Large source PDFs and raw archives stay outside Git. No researchers were contacted and no discovery claim was published.
