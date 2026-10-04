```text
Document:    A Steiner Quadruple System Route to C(16,5,3)
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      9169a2c0e7331589736da59e8b33b5cfc7fd763dac287cb3e73c493fd400ca3c
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Concrete proposal

Search for 64 five-point blocks drawn from extensions of two nonisomorphic
Steiner quadruple systems on 16 points. The audited union contains **1,744
blocks**, including **1,504 outside the earlier 528-block circle pool**. This
tests a different construction family without requiring a translation orbit,
regular point counts, a particular core, or a fixed number of extensions of
each quadruple. No 64-block cover has been found or claimed here.

This is promising as a bounded experiment because each smaller design covers
all 560 triples exactly once with 140 four-point blocks, and its lifted pool has
only 1,680 variables. The second seed introduces blocks unavailable in the
affine seed while increasing the combined pool to only 1,744. There is no
evidence yet that this restriction contains a 64-block cover.

## Primary literature

Petteri Kaski, Patric R. J. Östergård, and Olli Pottonen,
**The Steiner quadruple systems of order 16**, *Journal of Combinatorial Theory,
Series A* **113**(8), 1764–1770 (2006),
[DOI: 10.1016/j.jcta.2006.03.017](https://doi.org/10.1016/j.jcta.2006.03.017).

The [author's manuscript](https://koti.kapsi.fi/pottonen/sqs16.pdf) was retrieved
2026-10-04 at 05:15:13.397789 UTC. It redirected to
`http://pottonen.kapsi.fi/sqs16.pdf`. Its SHA256 is
`5f7ac51535fe88d86664c97862b45709b228fcaf0c1da10a4ab2eded231f30b9`.
The file is 138,807 bytes. The manuscript identifies itself as the author's
version, not the final publisher layout.

- Manuscript page 2 defines S(3,4,v) and states that SQS(16) has 1,054,163
  isomorphism classes.
- Section 2, manuscript page 3, describes extension of Steiner triple systems
  on 15 points to quadruple systems using exact cover.
- Section 3, manuscript page 6, discusses the incidence-matrix rank.
- Table 4, manuscript page 12, lists one rank-11 class and fifteen rank-12
  classes, with further classes at higher ranks.

Pages 2 and 12 were rendered and visually inspected; all manuscript text was
extracted. Crossref metadata confirms the journal, volume, issue, page range,
authors and DOI. OpenAlex provided the author-PDF location. `sources.json`
records the exact request URLs, UTC times, response hashes and byte lengths;
`citation.json` preserves the bibliographic fields.

The paper supports the availability of substantially different SQS(16) seeds.
It does **not** claim the 64-block covering construction proposed here. The
following parity trade and lift are explicit constructions checked locally.

## Two finite seeds

Label the points 1–16 and identify point p with the four-bit vector p−1.
The affine seed consists of the four-subsets whose vector XOR is zero. Any
three distinct vectors x,y,z have the unique fourth vector x XOR y XOR z,
so every triple belongs to one quadruple. There are 560/4=140 quadruples.

Take four pairs (1,5), (2,6), (3,7), (4,8). Selecting one point from each pair
gives 16 quadruples. The eight choices with an even number of second points
belong to the affine seed. Replace those eight by the eight odd-parity choices.
For any triple from three distinct pairs, exactly one choice of the fourth
pair completes each parity. Triples using two points from the same pair occur
in neither side. The two eight-block families therefore have identical triple
incidence, so replacement preserves the Steiner property.

`check_sqs_lift.py` verifies both seeds and the trade exactly. Their binary
incidence ranks are 11 and 12. Rank is invariant under point permutation,
so these two seeds are nonisomorphic. Both 140-block, four-point witnesses pass
the package verifier and standalone `scripts/check_cover.py` with k=4.

## Lift and restricted search space

For every quadruple Q, allow all twelve five-blocks Q∪{p} with p outside Q.
A five-block cannot contain two quadruples of the same Steiner system: those
quadruples would share a triple. Thus each individual pool has exactly
140×12=1,680 distinct five-blocks.

Each triple has 30 possible covering blocks in an individual pool: twelve
extensions of its own quadruple, plus six other quadruples through each of its
three pairs, extended by the missing point. The two pools together contain
1,744 blocks. The union's triple-support histogram is 336 rows of size 30,
192 rows of size 32, and 32 rows of size 38.

The original affine pool intersects the previous 528-block circle pool in 240
blocks; the traded pool intersects it in 224. Their union intersects it in 240.
The union therefore adds 1,504 blocks outside that earlier pool. The previous
exhaustion of *translation-invariant selections* does not exhaust this model:
individual selected blocks here need not form translation orbits.

Five damaged-seed and nine damaged-pool controls are rejected. Each seed has a
simple 140-block five-point extension cover as a positive control; both covering
verifiers pass these controls. These controls establish the construction and
pool handling, not attainability of 64 blocks.

## Falsifiable computational test

`build_model.py` exports a Boolean variable for every union-pool block, in
increasing global lexicographic order among all 4,368 possible five-blocks.
The entire model is exactly one cardinality row selecting 64 blocks and all
560 triple-coverage rows. It has 1,744 variables and 561 rows, with no objective,
symmetry constraints, fixed blocks, point/pair regularity assumptions, or
one-extension-per-quadruple rule.

The authorized single pilot used seed **2026104001**, **180 seconds**, and
**one worker**, after a separate independent gate. OR-Tools **9.15.6755** returned
**UNKNOWN** after **179.996219 seconds**, with 2,931,385 conflicts and 285,376,336
branches. It ran from 2026-10-04 05:27:26.816023 UTC to 05:30:26.830236 UTC and
produced no witness. This result is inconclusive. No repeat search was run.

`run_pilot.py` binds the model, pool, source and gate hashes and refuses to
overwrite its run directory. `check_pilot.py` verified the recorded parameters,
response and artifact hashes, and rejected all **12 damaged-result controls**.
Its readback is in `pilot-readback.json`; the full result is in
`pilot-result.json`, whose SHA256 is
`889a8d576443116c37c3ad8c8668b79530cc12dd53e7e49130176cf79a6bc698`.
The raw run artifacts are in the scratch folder's `pilot-2026104001/` directory.

A witness must pass both covering verifiers. A timeout/UNKNOWN is inconclusive;
solver INFEASIBLE would apply only to this fixed union pool and would not be an
independently checked theorem. Failure in this pool cannot exclude other SQS
seeds or arbitrary 64-block families. No global lower bound follows here.

The frozen model SHA256 is
`d0a70c16b53c2399ed10eae2deb77b3c817e352a4fc950d7584291b3c249703f`.
The pool SHA256 is
`b1e0e13ac3787643b25e920d2ce8f83d7119dedcb3c78daaf8316e04510c68c6`.
`model-manifest.json` includes all 1,744 global block IDs, source revision,
OR-Tools version, source hashes, pool counts and the proposed budget.

The manuscript, rendered pages, quadruple witnesses, positive controls,
large pool/support lists and model are outside Git in
`experiments/scratch/new-construction-web-20261003/`. No researcher was
contacted, no large design archive was downloaded, and no result was published.
