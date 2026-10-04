```text
Document:    A Variable-Cardinality Search Route After the Pair-Deficit Pilot
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      1627110fc4d4b74997adff639c32fd191928d7cb056c6592f4028bea60ab6659
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Finding

A practical new route is a **two-drop/add-repair trajectory with configuration
checking**, independently implemented from the published NuSC algorithm. This
changes the search state and sequence of moves: a stalled 64-block family can
move through 62 and 63 blocks before returning to 64. It does not optimize D2.
No optimizer was compiled or run during this source review, and no 64-block
cover or new public bound was found. Implementation was separately authorized
after this review; it belongs in a new experiment, with its own controls/gate.

## Primary evidence

Chuan Luo, Wenqian Xing, Shaowei Cai and Chunming Hu, **NuSC: An Effective Local
Search Algorithm for Solving the Set Covering Problem**, IEEE Transactions on
Cybernetics 54(3), 1403-1416. The DOI was registered in 2022; Crossref records
the print issue as March 2024. [DOI](https://doi.org/10.1109/TCYB.2022.3199147).
The authors' [repository](https://github.com/chuanluocs/NuSC-Algorithm) identifies
the paper and supplies the implementation. Exact frozen source revision:
`fdacd80d92e7143b4fe305bddce471a1e8982e90`.

- [Main program](https://github.com/chuanluocs/NuSC-Algorithm/blob/fdacd80d92e7143b4fe305bddce471a1e8982e90/NuSC/main.cpp#L23-L34): when sets outnumber elements, defaults are combined-score coefficient 5, tabu tenure 4 and nominal novelty probability 0.1.
- [State updates](https://github.com/chuanluocs/NuSC-Algorithm/blob/fdacd80d92e7143b4fe305bddce471a1e8982e90/NuSC/wscp.h#L842-L970): add/remove operations update coverage, two scores and configuration flags.
- [Incoming choice](https://github.com/chuanluocs/NuSC-Algorithm/blob/fdacd80d92e7143b4fe305bddce471a1e8982e90/NuSC/wscp.h#L1114-L1180): sample an uncovered element, rank its carrier sets, exclude configuration-locked and recently flipped sets, and sometimes choose the second best.
- [Weights and trajectory](https://github.com/chuanluocs/NuSC-Algorithm/blob/fdacd80d92e7143b4fe305bddce471a1e8982e90/NuSC/wscp.h#L1214-L1342): weights rise for remaining uncovered elements after an add-only move; when adding would reach the incumbent cost, choose either a swap or two removals.
- [License](https://github.com/chuanluocs/NuSC-Algorithm/blob/fdacd80d92e7143b4fe305bddce471a1e8982e90/LICENSE.md): GNU GPL version 3, copyright 2022-present Chuan Luo. Upstream source is retained unchanged only in ignored research evidence. No upstream code is copied into the project's All Rights Reserved source. Any new implementation must be written independently from the described algorithm with attribution.

The retrieved `wscp.h` SHA256 is
`eaddccf48a4d973944fc6520846d401376c2931f29567777a15f4371de83c5a4`.
The full journal article was not accessible through the publisher in this
retrieval, so exact move claims above are attributed to the author source.

## Exact rule extracted for unit costs

Let c(T) be each triple's count and w(T) its positive dynamic weight. For an
unselected block B, score(B) is the sum of w over its uncovered triples and
pscore(B) is the sum over its singly covered triples. For a selected block,
score(B) is minus its weighted singly covered count and pscore(B) is minus its
weighted doubly covered count. Rank by 5*score+pscore, then by pscore, then by
the oldest flip time. Unit costs remove all cost-ratio complications. The
source scans all outgoing sets when fewer than 80 are selected, as here.

At a complete cover, remove redundant blocks first, record a better complete
incumbent, and remove one selected block to search for improvement. At an
incomplete family, sample an uncovered triple and choose an incoming carrier.
If adding alone stays strictly below incumbent size, add it and increment
weights of triples still uncovered. Otherwise choose an outgoing block. If
incoming weighted uncovered gain exceeds outgoing weighted unique loss, swap.
If it does not, remove two blocks sequentially, recomputing the second choice.
Later iterations add blocks back. With incumbent 65 this permits 64-to-62-to-63-to-64
walks; it does not by itself make 65/66 excursions.

Configuration flags start true. Any changed block re-enables every block that
shares a triple with it. A removed block is set false **after** those updates.
Incoming blocks also need age at least four steps. This is a neighborhood-change
memory, not a timer alone. Incoming choice uses 78 carriers for C(16,5,3).
The source initially keeps the first carrier as a fallback if all candidates
fail its filters; an independent implementation must make that fallback explicit.

Source details matter: there is **no weight forgetting or decay** after the
initial weight-one assignment. The source's novelty test is
`(random() % 100)/(double)101 < novelty_p` with `novelty_p = 0.1`, which selects the second best in 11 of 100 residue
cases, not an exact ten-percent Bernoulli test. A fresh implementation should
record whether it reproduces this 11/100 rule or makes a declared correction.
Do not describe a new decay schedule as part of the inspected implementation.

## What is new here

The current `scripts/heuristic_search.cpp:252-300` already samples a hole,
scores all 78 carriers against every outgoing slot, corrects shared triples,
uses tabu/aspiration and protected incoming blocks, and increments/decays
dynamic hole weights. That mechanism alone is not new. The native D2 pilot
instead uses random replacements and its stronger-cut surrogate. Earlier
protected novelty and pool recombination are also already recorded.

The distinctive combination is persistent variable cardinality, the two-drop
branch, coverage-redundancy pscore and configuration memory. An exhaustive text
search of current tracked-scope scripts, source, tests, docs and dated experiment
sources found no implementation named NuSC, pscore, configuration checking, or
variable-cardinality search. The existing removal/CP repair performs a bounded
neighborhood solve, not this continuous add/drop walk with retained weights.
This is evidence about inspected files, not every unavailable historical run.

## Other inspected leads and limits

- Nikolic, Grujicic and Dugosija, *Variable neighborhood descent heuristic for covering design problem* (2012), [DOI](https://doi.org/10.1016/j.endm.2012.10.026), [institutional record](https://rfos.fon.bg.ac.rs/handle/123456789/1006). Its abstract says systematic removal/addition of blocks and 13 improved bounds. The PDF is marked restricted access; no copy was requested and no exact unread rule is inferred.
- Shaowei Cai's [SoCS 2021 tutorial](https://lcs.ios.ac.cn/~caisw/Talks/SOCS2021talk.pdf), pages 20, 26, 46 and 52, explains configuration flags, after-removal hole selection for vertex cover, and the weakness of basic configuration checking in dense neighborhoods. Page 46 was rendered and inspected. This supports the distinction from ordinary tabu; it is not a NuSC performance claim for this target.
- Gupta, Lee and Li, [*A Local Search-Based Approach for Set Covering*](https://arxiv.org/html/2211.04444v1), sections 2 and 3, gives a different theoretical route: maintain a partition of element responsibilities and accept harmonic-potential improvements after adding one or two subsets. It has approximation guarantees, not a practical guarantee of reaching 64. It was not selected over the concrete NuSC implementation.

Raw Google requests returned script/interstitial pages; Bing produced irrelevant
keyword results and DuckDuckGo no usable result text. A rendered Google query
located the author repository, which was then checked directly. Search results
and AI summaries were used only as pointers, not evidence for algorithm claims.
The fresh HTTP target-table request was challenged; the prior independently
recorded live entry remains 61 through 65, but is not represented as a fresh
successful HTTP lookup here. No absence-of-improvement theorem follows.

## Prepared pilot boundary

Start with the pinned, double-verified 65-block Belic cover, all 4,368 blocks
eligible, labels 1-based and lexicographic IDs. Use unit costs and seek any
actual complete cover of size at most 64. The newly authorized preparation
budget is two sequential 120-second runs, seeds 2026104701 and 2026104702,
stopping the entire campaign at the first such verified cover. No timed run
is permitted before separate independent controls and root's gate.

Save the best complete cover, raw best exact-64 partial, separate four-core-cap
admissible best exact-64 partial, and actual final state including cardinality.
The cap-55 theorem is for full64 covers. It must not be imposed on65/66 states,
extrapolated to55+(size-64), or used to constrain smaller intermediate states.
Use it only to label exact64 records; every claimed cover still requires both
covering verifiers. Any incomplete run remains inconclusive.

`sources.json` preserves URLs, timestamps, byte hashes, failures and source
identity. Full upstream code, PDFs and raw responses remain in ignored
`experiments/scratch/post-d2-literature-20261004/`. No researcher was contacted,
no account created, no discovery published, and no external program executed.
