```text
Document:    C(16,5,3) Continued Research Checkpoint
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      83fe6813e3dafa45984b7062a7268c217fdb8054054625e4e7e17cea737e1174
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Research continuation

The goal is still open: no verified64-block C(16,5,3) cover has been found. The best unrestricted partial cover still covers557 of560 triples. The best point-essential regular candidate still covers552. No global nonexistence claim follows from these experiments.

## Independently checked reductions

The published four-class degree19 link classification is retained. For two degree19 points sharing six blocks, all576 second links reduce to270 ordered representatives. An independent incidence-graph audit and270 explicit relabelings confirm196 classes after swapping the anchors.

Exact rational duals exclude four fixed32-block families. Every dual was replayed against all4368 possible added blocks with a standard-library checker. Independent exhaustive weighted trees exclude two more fixed families, using279 checked nodes. These are six local exclusions, leaving190 of the196 classes without such a certificate. They do not cover every degree19 configuration.

In the full regular20 branch, triples occurring six or seven times are vertex-disjoint. Sevenfold triples have an exact seven-block form, and their distinct outside hubs imply4*n7+3*n6<=16. The earlier eight-hole seeds have n7=3,n6=2, so this pattern must change before they can become full covers.

A sevenfold triple leaves three local families, each with13 quadruples on13 points and degree four at each point. A valid non-projective-plane local family was found. Two independent arithmetic enumerations show that no such family can omit both edges of the relevant two-edge star: all32235 possible Gram-matrix excess patterns have nonsquare determinant. In the point-essential branch, at least two local families must therefore omit complementary star edges.

## Recorded searches

- Four single-link runs of300 seconds,36 double-hub64 runs, and eight double-hub65 runs found no cover. The two fast double-hub negative results were subsequently checked by independent trees; all other negative solver outcomes in this batch are timeouts.
- The regular CP model with aggregate bounds retained an eight-hole seed after600 seconds. Native SAT with those bounds timed out after600 seconds. These outcomes are inconclusive.
- The first local search made41 attempts without changing a block. A second23-attempt run, with tie-breaking that favors new blocks, also kept its eight-hole seed.
- Three normalized sevenfold-triple CP runs, each300 seconds, returned UNKNOWN. Their encodings, optional heavy-count flags, fixed block IDs, pair equations and archived models passed a separate audit, including byte-identical model rebuilds.
- The longer-move heuristic still found no seven-hole qualifying state. It did find a ten-hole state satisfying the heavy-count inequality. All saved candidates were checked by both covering verifiers and a separate degree/pair/private-triple recount.

## Current direction

The next construction search combines three verified local13-point families and solves for18 additional blocks. It includes a known non-plane family and sampled projective-plane families. These template pools are restricted construction attempts, not a classification of all full covers. Local-family classification and independent model checks remain separate tasks.

Compact certificates, source snapshots, metadata, hashes and logs are under `experiments/2026-10-03`. Large raw solver models remain in ignored scratch directories. The branch remains isolated and has not been merged or pushed.
