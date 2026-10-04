```text
Document:    Bounded LP-Guided Link Switch Pilot
Version:     v1.0.1
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      531a9bab4eb7e08b339283659887ef9c46a429f453b0141dba57cb0cd10e64cf
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Three bounded LP-guided link-switch rounds

The elastic LP objective improved from 10.627554709636422 to 9.80113812280173,
then to 5.575882992498541. The third round's 20 selected neighbors did not improve
it. All 60 LP evaluations returned numerical OPTIMAL, consuming 8.514734171 solver
seconds and about 10.05 wall seconds. No exact fractional feasibility or covering
witness was found. Only 20 of the final 136 neighbors were selected in round 3,
so this is not an exhaustive local optimum.

## Method and evidence

The original ten-hole pattern had the best comparable recorded elastic score:
10.627554709636422, compared with 12.64569999478813 for the later ten-hole pattern
and 16.68585525272344 for the newest native 14-cut survivor. Exact dual gaps are
lower bounds and were not substituted for those numerical objectives.

A neighbor replaces two disjoint edges in one of four seven-edge anchor links
with either cross pairing. This preserves each outside-point incidence. The
finite generator rejects candidates outside the 276-block heavy universe,
duplicate blocks, or nonanchor heavy multiplicity above two, then deduplicates.
It maps each heavy tuple to the same independently audited 697-row completion
LP with 1,200 ordinary variables. Only the heavy contributions to row bounds
change. All six hub residual graphs stay permitted.

All neighbors are ranked by the maximum positive violation of the 14 checked
cuts divided by 1,000, then by lexicographic global heavy IDs. The signed row
weights of every certificate are bounded by 1,000, making each normalized
violation a valid lower bound on the LP's total L1 row slack. The top 20 are
selected per round. A fresh one-worker GLOP model solves each selected elastic
LP with a one-second limit. Only numerical OPTIMAL objectives select improving
states. The caps were three rounds, 60 evaluations and 30 accumulated solver
seconds. The runner saves all neighbor rankings and numerical vectors, checks
box bounds and recomputes each elastic residual, and attempts exact rational
primal checks if the numerical residual reaches zero.

The independent generator gate in `../lp-guided-link-switch-independent/`
re-enumerated all 132 initial neighbors, directly rebuilt 133 sets of 697 row
bounds, and replayed all 14 cut scores and the first 20 selections. The subsequent
neighborhoods contained 133 and 136 valid neighbors. `readback.py` rebuilt support
counts and directly checked all 60 vectors, objective values, selected improvements,
budgets and artifact hashes without another solver call. A damaged out-of-box
vector was rejected. Independent final-point review is recorded separately by
the exact-search agent.

Before the first optimizer call, runner v1.0.0 stopped because in-memory tuples
were compared directly with JSON lists. JSON-normalized equality fixed only that
preflight assertion in v1.0.1. No raw run directory or solver call existed at the
failure. Hash-identical pre-fix source and observed failure facts are preserved
under `experiments/scratch/lp-guided-link-switch-preflight-20261004/`.

The prior native template move family already preserved outside degrees, but
used hole/structural heuristic scores. Prior mixed-MIP and twelve-tuple LP screens
also differ from this local LP-fitness search. No earlier implementation of this
LP-guided two-edge-switch method was found in the 860 indexed experiment files,
the targeted C++ source, or the research notes inspected. This is a repository
scope statement, not an exhaustive literature novelty claim.

## Files and limits

`proposal.json` binds the original seed, checked model, basis oracle, cut bundle,
compiler-independent source hashes, initial neighborhood and ranking. `result.json`
records all selected results. `readback.json` records fresh numerical checks.
Complete rankings, floating-point primal vectors, frozen source snapshots and
start metadata are under the ignored `experiments/scratch/lp-guided-link-switch-20261004/`.
The provisional count probe of the later seed is preserved separately in ignored
scratch. The 60-evaluation run was not repeated.

This is a heuristic search within a regular four-sevenfold family. A lower
elastic objective is progress in that relaxation, not a covering design and not
an unrestricted lower bound. This pilot did not save dual vectors; any later
exact dual diagnostic is a separate, explicitly bounded experiment.

- `prepare.py` SHA256: `cd42848df3e6faaa19b510062fc97a8c7ac323193875e0809fbccdfa8b4dbd68`
- `proposal.json` SHA256: `46839a033b76abf0d2cca0974f67e021e80b975d6f7861664ed0e0b6f80624b0`
- `run.py` SHA256: `da0861952b988fe84124fd563a31659b202573793867326f40464b59346dd88a`
- `result.json` SHA256: `98f7d50da47d4584642d8316504102b6fa96aa529559938003060b102d3539bc`
- `readback.py` SHA256: `3742a055660d9ad8d18f9bcf390192e738a3e74bcff26ee8c9809069c212698b`
- `readback.json` SHA256: `1d1bf9614c1af1f9d36819fd2e799b8763dfd7ed6b7bf165a25955a701ea8a7e`

The executed numerical reader is preserved as `readback-executed-v1.0.0.py` in
the preflight scratch directory. Reader v1.0.1 only splits a 101-character scope
literal for Ruff; the frozen readback JSON remains unchanged and binds the
executed source. Current reader SHA256: `ac4d92d83a66511209f63ea41e292c8daeb736ab6a192809961ec06b4ca0268b`.
