```
Document:    Twelve Cut-Survivor LP Screens and Fourteen-Cut Bundle
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      2900728525068c672472afb160ee5c4c96b5d01c1e7443f1c56a5c29cd220504
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Twelve cut-survivor LP screens

All twelve distinct labeled heavy tuples surviving the two previously checked
labeled cuts are infeasible in the regular-family LP relaxation. Each conclusion
has an exact signed-row certificate. A separate replay reconstructs all twelve
models and rejects 132 damaged certificates. No fractional feasible witness was
found. No CP or native search ran.

This result concerns these fixed heavy tuples in the degree-20 regular
four-sevenfold family. It is not a global lower bound, a first-link exclusion,
or evidence that a 64-block cover cannot exist. All six hub graphs remain in the
relaxation. The official first-link registry remains unchanged.

## Inputs and model gate

The source inventory has 45 saved states, 32 distinct full families and 17
labeled heavy tuples. The original cuts separate five different tuples, leaving
the twelve considered here. Deduplication is labeled equality, not isomorphism.

`build.py` uses the frozen new-tuple model as a structural template, shifting
only finite row bounds by the difference in fixed-heavy incidence. Before any
solve, the hash-pinned independent oracle
`../lookahead-cut-independent/check.py` reconstructs every model directly from
its saved 64-block state and checks the complete protobuf structure. Six damaged
models are also rejected. Each model has 1,200 ordinary variables in original
global lexicographic order and 697 rows: cardinality, all 560 triples, all 16
point degrees and all 120 pairs. The oracle retains all 276 possible heavy
columns in its symbolic incidence basis and all six hub graphs.

`manifest.json` binds each labeled tuple, its saved seed, model hash, input
inventory, builder, source model, source gate and independent oracle. Large
models and numerical vectors remain outside Git in
`experiments/scratch/cut-survivor-lp-screen-v1.0.0/`.

## Bounded LP pass

`run.py` and `lp_core.py` use OR-Tools GLOP 9.15.6755, one worker, sequential
cases, seed 2026104, with ten seconds for each feasibility phase and at most ten
seconds for each elastic phase. The announced maximum was 240 solver seconds
and approximately 300 wrapper seconds. The 24 phases used 3.101360 solver seconds
and 5.685190 wrapper seconds. Every feasibility phase reported INFEASIBLE and
every elastic phase OPTIMAL, but those numerical statuses are not the proof.

All twelve exact certificates work with denominator 1000. For signed row weights
`w`, lower bounds are chosen for positive weights and finite upper bounds for
negative weights. The combined ordinary-column coefficients are `a`. Since
`0 <= x <= 1`, every completion would require
`sum(w * bound) <= sum(max(0, a))`. Each saved certificate violates this
inequality by the strictly positive exact gap below.

| Case | Heavy hash prefix | Best saved holes | Exact gap | New cut RHS |
| --- | --- | ---: | ---: | ---: |
| 00 | `2ff8e2399857` | 31 | 1637/100 | 83389 |
| 01 | `436d3e563865` | 42 | 17977/1000 | 82158 |
| 02 | `e32b0008b103` | 43 | 11299/1000 | 71351 |
| 03 | `dabecf9d9870` | 43 | 12041/1000 | 85207 |
| 04 | `17587e6eb146` | 48 | 15189/1000 | 83240 |
| 05 | `1d1d2b11ba6e` | 50 | 15721/1000 | 92962 |
| 06 | `e05445be39b8` | 50 | 2041/100 | 80551 |
| 07 | `3c4dcba7c7b3` | 54 | 16547/1000 | 79476 |
| 08 | `10e7e7381db4` | 54 | 7757/500 | 86813 |
| 09 | `8f6d6eb0f6b1` | 56 | 8967/500 | 86531 |
| 10 | `1db1a6beafa5` | 61 | 7667/500 | 90118 |
| 11 | `817b67af75d6` | 61 | 4713/250 | 80687 |

`results.json` records every phase, budget, timing, solver/Python version,
source revision, code hash and exact result. `cases/*/dual.json` contains the
compact signed certificates and model/tuple bindings.

The executed runner is preserved byte-for-byte as
`scratch/cut-survivor-lp-screen-v1.0.0/lp-frozen-run.py` relative to `experiments`.
After the run, one long descriptive string in the tracked wrapper was wrapped
for Ruff. The executed and tracked source have identical Python ASTs, which
`check.py` verifies. The recorded execution hash refers to the frozen copy.
No numerical solve was repeated after this formatting-only change.

## Separate replay and negative controls

`check.py` does not import the LP helper or call any solver. It reuses only the
previously independent model oracle, then computes the certificate sums from
the reconstructed symbolic rows with Python integers and fractions. It binds
all input hashes and exact totals, rejects malformed or duplicate row weights,
and requires a strictly positive contradiction. Eleven damaged variants of
each certificate test altered model, tuple and manifest bindings, zero
denominators, altered RHS/box/gap, duplicate/dropped weights, out-of-range rows
and a false claim flag. All 132 are rejected. See `audit.json`.

## Reusable fourteen-cut bundle

`derive_cuts.py` uses the same audited symbolic row basis to separate each
signed sum into an unconditional constant `K`, ordinary coefficients `a`, and
heavy coefficients `c`. Every regular completion must satisfy
`sum(c[b] * h[b]) >= K - sum(max(0, a))`.

`cut-bundle.json` includes all twelve new inequalities plus unchanged copies of
the original two mathematical cuts. The first two coefficient vectors,
constants, bounds and ordinary sums are re-derived and checked against their
frozen source cuts. The original source files are preserved. Shared lists of
276 heavy blocks/global IDs and 1,200 ordinary global IDs appear once. Each cut
binds its dual, source model, source heavy tuple, and source cut where relevant.
Ordinary coefficient vectors are represented by hashes of
`json.dumps(vector, separators=(',', ':')).encode()` with UTF-8 and no newline.

`cut-bundle-saved-tuple-screen.json` records each of the fourteen labeled cut
scores for all seventeen saved heavy tuples. All seventeen are separated.
The original cuts separate three and two tuples respectively; each new cut
separates its own source tuple and none of the other sixteen labeled tuples.
This file does not perform an additional symmetry-orbit screen. Independent
root replay of the bundle is recorded separately by the coordinating agent.

## Reproduction

`uv run python experiments/2026-10-03/cut-survivor-lp-screen/check.py` replays the
certificates without any solver call. The builder, solver runner and cut
deriver reject existing outputs to preserve frozen artifacts. Do not rerun the
LP screen over its existing output directory. Use a new version directory for
new experiments. The narrow Ruff check passed; repository-wide checks and Git
integration are owned by the coordinating agent.
