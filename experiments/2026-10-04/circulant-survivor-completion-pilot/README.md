```text
Document:    Four Conditional Completions of Circulant Survivor Links
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      5c083cfb8920a2d0c0eaf1e6db04366644806f10133645a8b1456f6852cb9c33
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Prepared conditional completion pilot

The completed iterative row-propagation pass left 1,096 unresolved pairs among
the chosen four-witness point-link images. They comprise 410 C4-leaf cases,
658 triangle-path2 cases and 28 triangle-two-leaves cases. No C5 case remains in
this survivor set. These fixed points do not assert that a completion exists.

The selector picks the case with the fewest free variables for each available
core type, breaking ties by the saved pair ordinal. It then picks the lowest-free
case in a new excess-profile orbit, when available. It excludes repeated images
under the audited reflection fixing point 1. The full selection census,
reflection pairs, profile-orbit representatives and chosen records are saved in
`selection.json`. This is case selection only; it adds no model restrictions.

| Case | Core type | Pair ordinal | Partial ID | Profile ID | Free after propagation | Seed |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | C4-leaf | 55433 | 1585 | 465 | 325 | 2026106701 |
| 2 | triangle-path2 | 48366 | 1400 | 294 | 308 | 2026106702 |
| 3 | triangle-two-leaves | 51739 | 1487 | 466 | 378 | 2026106703 |
| 4 | triangle-path2 | 135193 | 3816 | 1238 | 321 | 2026106704 |

All four selected cases belong to different excess-profile orbits. The seed
audit found no earlier use of these four seeds in 25,269 existing experiment
source, JSON, Markdown, parameter and log files, including ignored scratch.

## Exact full-domain models

Each model contains all 4,368 Boolean pentad variables in lexicographic order:
560 exact global triple equations with demand 2 on the chosen 80 excess triples
and demand 1 otherwise; one exact cardinality equation of 64; and 1,365 equations
fixing every point-one membership to the chosen 20-block partial. Thus each
model has exactly 1,926 linear equations. All 3,003 point-avoiding variables keep
their original Boolean domains. There are no propagation-based restrictions,
hints, objectives, or cover-invariance equations.

Each input partial passes both independent coverage checks with 20 blocks,
185 covered triples and 375 holes. Its 455 outside residual demands are
nonnegative and sum to 440. Any solver candidate must satisfy all 560 exact
profile equations and all fixed memberships, then pass both complete-cover
verifiers before a witness is accepted.

## Frozen budget and evidence

Only root may launch after independent review:

```sh
uv run python experiments/2026-10-04/circulant-survivor-completion-pilot/run.py run
```

The wrapper makes four sequential calls, each with 30 solver seconds, one worker,
and its distinct saved seed. A separate 35-second process watchdog allows a
5-second SIGTERM grace before SIGKILL. There are no retries or budget transfers.
An exclusive launch receipt, direct-parent check and exclusive output directories
prevent a repeated run or ordinary direct worker invocation.

The manifest pins source, versions, all model and parameter files, input data,
selection, verification outputs, helper watchdog and seed audit. Model text stays
under ignored scratch. Runtime receipts retain exit states, logs, hashes and
solver status. UNKNOWN and timeouts are inconclusive. CP-SAT INFEASIBLE is not
an independently checked proof. These four attempts do not cover all survivors
and cannot establish unrestricted nonexistence.
