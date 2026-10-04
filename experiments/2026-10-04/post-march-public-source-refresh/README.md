```text
Document:    Post-March Public-Source Refresh for C(16,5,3)
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      1472ef84e1ec2a41c9416f653c188409ec4f1adbf8656c36b87325cc5646e35c
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Post-March public-source refresh

This bounded check found a live successor to the frozen Gordon archive, but did **not** verify its current `C(16,5,3)` entry. No new bound or candidate witness for that target was found in the accessible sources screened. This does not show that no later improvement exists.

## Live successor

[Covering Repository](https://coveringrepository.com/) says its historical data through the end of March 2026 came from Dan Gordon, and that later improvements are tracked within the site. The homepage was retrieved on 2026-10-04 at 20:24:20 UTC. Its raw SHA256 is `6c296663b1ac3ff412bec8ff956ed8002a668a871edecb7fc07eb74eeac926ee`.

The [latest ordinary-covering improvements page](https://coveringrepository.com/systems.aspx?li=2), retrieved at 20:28:50 UTC, includes records dated through 2026-10-04. Raw SHA256: `65334bec1916b27ecd49f28050e103773d4ba7c96cfbc66324fbf8aebd0e52f8`. This is a recent slice, not a full history. The absence of a target row cannot establish its current bound.

The direct read-only target lookup `https://coveringrepository.com/systems.aspx?v=16&k=5&t=3&m=3` returned HTTP 403. The exact request timestamp and response body were not saved before that exception; surrounding successful receipts bracket it between 20:28:50 and 20:30:54 UTC. This lookup stopped. No sign-in, payment, contact, challenge bypass, or alternate-path access was attempted. The previously checked **61–65** range remains explicitly a **March 2026 archive value**, not a freshly checked current claim.

## Recent primary sources screened

| Source | Accessible finding | Scope |
| --- | --- | --- |
| Richard Bean, [A tight single-change covering design with block size 6](https://arxiv.org/abs/2607.10978), 2026-07-13 | A tight design at `v=26,k=6`, with SAT search and negative results at `v=21`. | No target improvement appears in the abstract. |
| Wang, Ma, Wang, Tian, [Generalized group divisible covering designs](https://doi.org/10.1007/s10623-026-01863-5), 2026-06-03 | Strength 2 with block sizes 3 and 4; strength 3 with block size 4. | Public abstract inspected; full text is subscription restricted. |
| Ta and Vu, [Near-optimal covering sequences](https://doi.org/10.1007/s10623-026-01934-7), 2026-09-15 | Cyclic sequences whose windows form Hamming covering codes. | Public abstract inspected; full text is subscription restricted. |
| Guangmin Zhu, [Construction of Covering Sets](https://doi.org/10.5539/jmr.v18n1p59), March 2026 | Optimization of covering sets, with a generalization to Gaussian integers. | Abstract only; full text not inspected. |
| Martin Anthony, [Counting and Covering in Nearest-Neighbour Representations of Boolean Functions](https://arxiv.org/abs/2609.23094), 2026-09-19 | Covering numbers in Boolean nearest-neighbour representations. | Primary API abstract only. |
| Ralph Stömmer, [Tackling the 6/49 Lottery and Debunking Common Myths with Probabilistic Methods and Combinatorial Designs](https://arxiv.org/abs/2603.24170), first posted 2026-03-25, updated 2026-05-31 | Lottery parameters involving 49 points and blocks of size 6. | Primary API abstract only. |

The arXiv API query for `all:"covering designs"` over 2026-03-01 through 2026-10-04 returned 12 entries. Most were unrelated title/abstract matches. The query included March to retain later revisions to March papers, but it cannot find every later revision to older submissions. Crossref was used only to discover publisher pages. Its fuzzy matches are not mathematical evidence. Bing misinterpreted the exact mathematical query; Google returned a JavaScript/retry page. Neither supplied useful negative evidence.

## Evidence and limits

`source-checks.json` records source URLs, retrieval timestamps, raw hashes, accessible claims, and explicit limits. Every saved successful-response hash was recomputed from the ignored raw file. Raw network pages remain under `experiments/scratch/post-march-covering-source-check-20261004/`; they are not committed. The failed target request is recorded separately because its raw response was not saved.

No solver ran for this source refresh. No new construction or impossibility theorem was established. A later permitted direct check of the maintained target entry remains useful; the current evidence cannot replace it. No researcher was contacted and nothing was published externally.
