```text
Document:    Primary-Source Review of a Distinct Covering Search Move
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      5f4ca5c25803aa8ba2f35f0cdfd7254e21495c2d58e54bac67c134f8ab5eddef
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Finding and proposed route

A **forced-novelty phase with protected incoming blocks, followed by unrestricted
repair**, is a concrete literature-backed mechanism not found in the current
native search. It preserves 64 distinct blocks and needs no degree or symmetry
assumption. It is an implementation opportunity, not evidence that it will reach
a cover. The same primary source already reports a three-hole result for this
exact instance.

The strongest available three-hole seeds reportedly share 62 of 64 blocks
(confirmed by the concurrent heuristic review). Their union has only 66 blocks,
so recombining those two alone supplies little diversity. Prior escape searches
also reached low overlap with the original labeled core without necessarily
escaping its structural family. The proposed experiment must therefore measure
structure as well as labeled overlap.

## Freshly inspected primary sources

**Chaoying Dai, A multilevel cooperative parallel tabu search algorithm for the
covering design problem, University of Manitoba master's thesis (2006).**
[Institutional record](https://mspace.lib.umanitoba.ca/handle/1993/20757),
[full thesis](https://mspace.lib.umanitoba.ca/bitstreams/59691761-79b2-41cc-b62b-d4e64b50ed85/download).
Retrieved again on 2026-10-04 at 06:19:11 UTC. The server resolved the PDF to its
public bitstream-content endpoint. SHA256:
`7facea53363f6f8803a2b2b92359829858a77418378292fee92c7af2de8fcce1`.
This is the same primary document as the earlier project review, now checked
against the proposed mechanism and its result on the exact target.

- Printed page 62 (PDF page 71): a restricted phase inserts blocks belonging
  strictly to the larger level, outside the smaller elite pool. Incoming blocks
  cannot leave during that phase. The phase lasts at most the number of selected
  blocks and may substantially worsen cost. General search follows from the
  resulting state, rather than restarting at the previous elite.
- Printed pages 64-65: the author attributes the largest observed contribution
  to improvement to transferring a solution from the small pool to the full
  pool, where new replacements become available. The discussion explicitly
  warns that excessive overlap among elite solutions reduces search diversity.
- Printed pages 65-66, Figure 6.6: a restart pool combines recent elite blocks,
  random blocks from outside the small pool, and filler from the small pool.
  A random collection of the target number of blocks is optimized in that
  pool before transfer to another level. These are distinct pool-management
  phases, not merely a different random seed.
- **Printed page 76 (PDF page 85), Table 7.2:** the row for `3-(16,5,1)` records
  lower bound 61, upper bound 65, target block count 64, and **cost 3**. Cost is
  the number of uncovered triples. This is a historical heuristic result,
  not a covering witness or an impossibility proof. Pages 62, 65, 66 and 76
  were rendered and visually read.

**Kamal Fadlaoui and Philippe Galinier, A tabu search algorithm for the covering
design problem, Journal of Heuristics 17(6), 659-674 (2011).**
[DOI](https://doi.org/10.1007/s10732-010-9150-2),
[author-institution record](https://publications.polymtl.ca/16914/).
Both pages were retrieved on 2026-10-04. The publisher abstract describes a
faster, less memory-intensive neighbor evaluation and more than 50 improved
upper bounds. The requested article PDF redirected to the publisher's
subscription preview. The institution supplies an external link, not full
text. Consequently, the abstract does not support importing a specific
unread weighting, ejection-chain or move rule.

**Kari Nurmela and Patric Ostergard, Constructing Covering Designs by Simulated
Annealing, Helsinki University of Technology, Digital Systems Laboratory,
Series B, Technical Report 10 (1993).**
[Institutional record](https://research.aalto.fi/en/publications/constructing-covering-designs-by-simulated-annealing/).
The record confirms title, authors, year and report number. No full-text link
was exposed there, so no new cooling schedule is attributed to it.

**Dan Gordon, Covering Designs.**
[Maintainer page](https://dmgordon.org/covering-designs/).
Freshly read as a primary repository pointer. It links the successor database
and the Gordon-Kuperberg-Patashnik construction paper, DOI
[10.1002/jcd.3180030404](https://doi.org/10.1002/jcd.3180030404).
This pointer alone supplies neither a new local-search implementation nor
evidence about the present pilot's quality. No live bound refresh is claimed.

## Comparison with current code

`scripts/heuristic_search.cpp:144-155` alternates baseline and best states,
performs random perturbations, and sometimes randomizes the complete state.
The random best-state perturbation does not require incoming blocks to lie
outside an elite union and does not protect all of them through a separately
defined forced phase. `scripts/heuristic_search.cpp:251-298` has directed tabu,
changing uncovered-triple weights, decay, and a short incoming-block tenure.
Changing those existing weights or running them longer is not the proposal.

`src/covering64/search.py:53-192` performs monotone removal and repair, replacing
`r` blocks by at most `r-1`. It is not a variable-cardinality plateau walk.
The native target count is fixed during a run. An exhaustive Graft search of
954 indexed files found no hits for `recombin`, `relink`, `tempering`,
`variable.cardinality`, or `replica_exchange`; the relevant documentation
contains the earlier proposal but no recorded implementation. C++ and Markdown
were also searched directly. These checks establish what was found in the
current code and notes, not that every old scratch artifact was exhausted.

The separately reviewed whole-point-star repair remains an instance-specific
alternative: all three current holes contain one point. It changes which
large neighborhood is scheduled. Protected novelty changes the trajectory
through fixed-cardinality states. Neither is a new global feasibility model.

## One bounded adaptation to prepare if selected

1. Freeze the two verified three-hole seeds and their exact 66-block elite
   union `E`. Start from one seed with exactly 64 distinct blocks.
2. Perform exactly **16 forced replacements**. Each incoming block must be
   outside `E` and absent from the current state. A block inserted during this
   phase cannot be removed until the phase ends. Select the lowest unweighted
   hole delta among permitted moves, with a fixed seeded tie rule. Thus the
   completed phase retains at least 16 distinct blocks outside `E`.
3. Release both temporary restrictions. Run the established tabu repair on
   all 4,368 blocks from this worsened state, with its weights reset and a
   separate fixed time budget. Keep the best unweighted state seen in either
   phase. Do not silently reset to the original seed when forced cost rises.
4. Before a timed pilot, independently check the 16-step trace, exact deltas,
   protected-block invariant, distinctness and rollback controls. Save seed,
   source, binary, input hashes, phase costs, elite overlap and heavy-profile
   diagnostics. Verify every claimed cover through both covering checkers.

The choice of 16 steps is a **local experimental hypothesis**, not a parameter
validated by the thesis for this instance. This proposed bounded phase was
not implemented or run during this review. No fixed degree, incidence profile,
orbit, or core restriction would remain during repair. A failure would remain
inconclusive.

A strict triple trade preserves every triple's multiplicity, so applying only
such a trade cannot lower the number of holes. It could diversify a later repair
trajectory, but calling a triple-preserving trade itself a hole-reducing move
would be incorrect. No detailed covering-design ejection-chain implementation
was verified from the accessible primary sources in this review.

## Provenance

`sources.json` records request URLs, response URLs, UTC retrieval times, file
lengths and hashes. PDFs, extracted text, page renders and HTTP responses remain
outside Git in `experiments/scratch/local-search-methods-20261004/`.
One broad Crossref query returned HTTP 429; it was not retried. No researcher
was contacted, no executable was downloaded, and no optimization was run.
