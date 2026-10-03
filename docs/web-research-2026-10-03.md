```text
Document:    Public Sources and Search Methods for C(16,5,3)
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      91085e4dca2eb1e36d3699644669289b23b83dbd1dfcaf0f4afc4ec6bf572e18
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

## Scope and result

Public web research ran on 2026-10-03, approximately 17:43-17:57 UTC. The current maintainer-recommended table still records **61 <= C(16,5,3) <= 65**. No 64-block witness was found. This is a report of the inspected sources, not an exhaustive literature survey or a proof that 64 blocks are impossible. No researcher was contacted, no account was created, and no result was submitted or published.

## Current table records

Dan Gordon's [covering-designs page](https://dmgordon.org/covering-designs/) says that Giovanni Acerbi's [Covering Repository](https://coveringrepository.com/) includes the old database and more recent improvements. Gordon's page displayed a site update of 2026-09-03. The replacement repository says historical records through March 2026 were imported from Gordon, with later improvements tracked there. The legacy `ljcr.dmgordon.org` host did not resolve during this retrieval.

| Source, inspected 2026-10-03 | Parameters | Recorded size | Recorded lower bound | Attribution and date |
| --- | --- | ---: | ---: | --- |
| [Current target entry](https://coveringrepository.com/systems.aspx?v=16&k=5&t=3&m=3) | (16,5,3,3) | 65 | 61 | Rade Belic; 06/08/1997 |
| [Target history](https://coveringrepository.com/history.aspx?id=110841) | (16,5,3,3) | 65, previously 68 | 61 | Belic, 06/08/1997; JCD article, 14/11/1996 |
| [Smaller link entry](https://coveringrepository.com/systems.aspx?v=15&k=4&t=2&m=2) | (15,4,2,2) | 19 | 19 | Random Greedy Covering; 21/01/1997 |

Dates above retain the site's day/month/year display. The four-parameter definition is that every m-set intersects a block in at least t points. Because m=t in these rows, these are ordinary covering designs. Query URLs redirect to `systems.aspx` while retaining the requested filter in the browser session. The target's free download was linked as [record 108633](https://coveringrepository.com/download_system.aspx?id=108633).

The exact smaller value is **C(15,4,2)=19**, not 20. Thus a 64-block target cannot safely be restricted to replication 20 at every point. The elementary recursive count gives replication at least 19 and the lower bound ceil(16*19/5)=61. No stronger global lower bound was established here.

## Retrieved smaller witness

The 19-block witness is saved as `experiments/scratch/web-link-15-4-2.txt`, with the original numeric lines and 1-based labels. Source: [free download record 104489](https://coveringrepository.com/download_system.aspx?id=104489), retrieved through the public browser download at approximately 17:52:59 UTC. Raw SHA256:

```text
1356b649b573113168e61ce8f52814e9ccb945d6f78a3faab5b8c3543712d684
```

A separate Python enumeration checked 19 distinct blocks, four distinct labels in 1..15 per block, and all 105 pairs covered. Exactly 96 pairs occur once and nine occur twice. This check is for the smaller witness only, not either required C(16,5,3) acceptance verifier.

One proposed experiment appends point 16 to these 19 blocks, then searches for 45 further 5-blocks on points 1..15 to cover the remaining triples. This fixes one particular point link. Its failure would exclude only that fixed-link experiment; it is not a complete reduction of the unrestricted target.

## Concrete algorithm source

Chaoying Dai, *A multilevel cooperative parallel tabu search algorithm for the covering design problem*, University of Manitoba master's thesis, 2006. [Institutional item](https://mspace.lib.umanitoba.ca/handle/1993/20757); [open PDF](https://mspace.lib.umanitoba.ca/bitstreams/59691761-79b2-41cc-b62b-d4e64b50ed85/download). Retrieved around 17:54 UTC; metadata rechecked at 17:56 UTC. PDF SHA256:

```text
7facea53363f6f8803a2b2b92359829858a77418378292fee92c7af2de8fcce1
```

The following details were read in the full thesis. Page numbers refer to printed pages; PDF page numbers are nine higher. The parameter table on printed page 69 was also rendered and visually inspected because OCR distorted its numbers.

1. **Moves and evaluation (pp. 40-45).** Replace m points within one selected block; m=1 is the usual neighborhood. Store each block's sorted triple ranks and each triple's current coverage count. For replacing block A by B when lambda=1, compute `delta = number of triples in A\B with count 1 - number of triples in B\A with count 0`, where A and B in this formula denote their covered-triple sets. Shared triples do not change. Select a best admissible neighbor, including non-improving moves.
2. **Two tabu memories (pp. 45-46; Table 7.1, p. 69).** The first list records both the forward block exchange and its reverse; the second temporarily protects the incoming block from removal. Reported typical list lengths are 10-12 for the first and 5 for the second. These are experimental settings, not proven optimal values.
3. **Reduced block pools (pp. 52-57).** Search several nested subsets of the available blocks. Move the blocks of each good solution into the smallest pool and rebalance by evicting other blocks. An elite solution from a smaller pool becomes a starting solution for a larger pool. These pools are heuristic restrictions, not complete symmetry reductions.
4. **Forced novelty followed by repair (pp. 60-63).** When a search fails to improve, briefly permit incoming blocks only from the part of the current pool outside the next smaller pool. Protect each newly inserted block from removal for the remainder of this phase. The phase lasts at most b moves and can substantially worsen coverage. Follow it with ordinary search over the whole current pool, starting from that worsened state. This is a directed way to escape an elite-only basin.
5. **Recombination then expansion (pp. 62-66).** Good solutions often come from recombining blocks from several elite solutions. The thesis warns that excessive overlap among those solutions reduces diversity. It credits transferring a small-pool elite to the unrestricted pool with the largest contribution to improvements. A restart pool mixes blocks from recent best solutions, fresh random blocks, and filler from the small pool. Table 7.1 gives 20-100 random restart blocks and 2-60 tabu iterations for the restart-pool search.

The thesis formulation permits repeated blocks. The current project must retain its distinct-block rule, so incoming blocks already present must be rejected. The thesis's numerical gains concern its own tested instances; none of these passages establishes a 64-block result for this target.

## Suggested bounded experiments

These are adaptations to the present deficit-three plateau, not claims of source-tested parameters for this instance:

- Retain several independently obtained near-covers. Search their union plus 20-100 random blocks for a short period, then release all 4,368 possible blocks and repair. Keep the original solutions and seeds for comparison.
- Try a short forced-novelty phase with incoming blocks outside the elite union, protect each new block during that phase, then run unrestricted tabu repair. Record the phase length and temporary deficit rather than silently treating the worsening as a failed run.
- Evaluate m=2 replacements occasionally after m=1 stagnation. The thesis defines this neighborhood but notes its larger cost; this is a proposed use of it. For this instance, m=1 gives 64*5*11=3,520 directed moves, while m=2 gives 64*10*55=35,200.
- A weighted escape objective is an additional hypothesis, **not a method established by the inspected thesis**: increase weights of persistently uncovered triples and evaluate the same symmetric-difference delta with those weights. Always measure success by the unweighted count and the two independent verifiers. Reset or decay weights between restarts and record the schedule.

## Other primary sources and access limits

- Fadlaoui and Galinier, [*A tabu search algorithm for the covering design problem*](https://doi.org/10.1007/s10732-010-9150-2), Journal of Heuristics 17, 659-674 (2011). Publisher abstract inspected at approximately 17:46 UTC. It reports faster and less space-consuming neighbor evaluation and improved bounds for more than 50 instances. Full paper access was restricted; its exact algorithm details were not read and must not be inferred from the abstract.
- Their open [EPM-RT-2010-01 report](https://publications.polymtl.ca/2650/) contains the actual improved witnesses, encoded as lexicographic block indices, rather than the algorithm. [PDF](https://publications.polymtl.ca/2650/1/EPM-RT-2010-01_Fadlaoui.pdf), retrieved around 17:51 UTC; SHA256 `8209cd3f580f5fd174268163402b334a55eab41483025aad53bb3e13bfcbe6fb`. The inspected table contains no C(16,5,3) entry. Its witness format can be useful for independent checks on solver implementations.
- Margot, [*Small covering designs by branch-and-cut*](https://doi.org/10.1007/s10107-002-0316-z), Mathematical Programming 94, 207-220 (2003). Publisher abstract inspected around 17:46 UTC. It explicitly uses isomorphism pruning and reports a proof of C(10,5,4)=51 together with all nonisomorphic optimal designs. This supports studying complete isomorphism pruning, not imposing rotational symmetry on an unrestricted target. The full proof was not audited here.

Exact-parameter and cyclic-cover searches did not identify a source for a 64-block target. Search engines are incomplete; this absence is not mathematical evidence of nonexistence. Google returned a rate-limit page, while Bing and DuckDuckGo provided usable results. A Combinatorial Press page returned a browser challenge; its full text was not accessed. PDFs and larger fetched evidence remain under `/tmp/covering64-web`, outside Git. This report contains no claim based on the separate local symmetry experiments.
