```text
Document:    Registry-Filtered Fixed-g1 Nearest Master Launch Record
Version:     v1.1.1
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      c21838d89fa7e5647faa128068838219f6de326acf3d6f868f7a6dd012e546c6
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```
# Prepared fixed-g1 nearest master

This manifest freezes a new master with 276 heavy-block Boolean variables and
1,977 constraints: 605 original heavy-family conditions, 353 broad cuts,
1,000 independently replayed g1 cuts and 19 previously checked graph-1 link
nogoods. It minimizes the number of replaced heavy blocks relative to the
7.52051548546158 g1 incumbent. It imposes no distance constraint or radius.

Each proposed tuple receives all four registry classifications before LP.
An excluded seven-block anchor link adds only the graph-1-scoped inequality
that at most six of those seven block variables can be selected. Accepted
profiles use the exact fixed-g1 completion rows. Positive saved duals yield new
graph-1 cuts; numerical zero stops immediately for exact primal reconstruction.
The broad inventory is never changed by a branch-specific cut or nogood.

The proposed maxima are 50 admitted LP candidates, 150 master proposals, two
seconds per master call, one second per LP, 120 combined solver seconds,
160 wall seconds and one worker. The combined time cap can end the run before
the proposal or LP caps. The source, initial model, nogoods, inputs and baseline
are frozen in `manifest.json`. Preparation performed zero optimizer calls.

Execution requires a passed independent gate binding the source and manifest.
UNKNOWN/timeouts are inconclusive. A master FEASIBLE result does not prove that
its proposed tuple has the smallest replacement distance. No global lower-
bound or covering-witness claim follows from this preparation.

## Observed bounded attempt

The first two-second master call returned **UNKNOWN** during presolve, before
any branch, propagation or LP iteration. No heavy tuple, registry rejection,
completion LP, new nogood or new conditional cut was produced. The incumbent
remains 7.52051548546158. The attempt used **1.985302958986722 solver seconds**
and **3.33435866702348 wall seconds** and stopped under its frozen policy for a
master call without a candidate. No optimization was repeated.

The initial model contained 376,041 terms in long linear constraints. Its
logged dominated-linear and set-PPC presolve passes each used about 0.63 seconds;
the response reported zero branches and zero LP iterations. This is a solver-
startup time limit, not evidence of infeasibility or nearest-pattern optimality.
The initial model and full presolve/response/parameter logs remain frozen in
the raw directory. Launch revision was
`c80235d7fc403c6bdb9a7d06cf8134f6a267fae9`.

The independent postcheck in `../g1-nearest-master-independent/` passed the
exact model, parameters, response, raw hashes and budget recount. It confirms
one inconclusive UNKNOWN call with no downstream candidate or LP evaluation.
