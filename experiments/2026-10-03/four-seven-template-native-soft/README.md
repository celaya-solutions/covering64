```text
Document:    Complete Heavy Template Soft-Score Pilot Results
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      7ed342aa54434f5e4821ff28a4bf59afb8f4c9152cb6f57d57b244eb8a8a43d7
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Result

No cover was found. Both 300-second native pilots finished normally with one
worker per process. These are construction results only; they exclude no
covering family and establish no lower bound.

| Case / record | Holes | Soft score | Pair target L1 | Nonheavy excess | Max nonheavy count |
|---|---:|---:|---:|---:|---:|
| Matching seed | 21 | 155 | 30 | 4 | 3 |
| Matching raw best | 17 | 116 | 16 | 3 | 4 |
| Matching score best | 19 | 106 | 6 | 1 | 3 |
| Cycle seed | 19 | 134 | 24 | 3 | 3 |
| Cycle raw and score best | 12 | 92 | 12 | 4 | 6 |

Matching attempted 236,459,969 main-loop proposals with 472 restarts. Cycle
attempted 234,822,903 with 469 restarts. Full per-mode counters, pair vectors,
triple distributions, best hashes, and exact logged records are in `summary.json`.
The raw and score best records differ for matching. Cycle's four units of
nonheavy excess are concentrated in one triple occurring six times.

# Checks

The independent pre-pilot gate is in `../four-seven-template-native-soft-independent/`.
It checked the source difference, complete catalog membership, 42 existing and
37 fresh saved states, 16 operations, fresh sanitized builds, and 64 damaged
score/hole fields. Local preflight separately checked 42 snapshots and eight
forced moves/rollbacks, rejected 17 damaged inputs and 32 damaged score records,
and confirmed known seed scores. Both three-second sanitizer runs had empty
stderr. The prior native v1.0 source and evidence were left unchanged.

The full pilot audit checked all 118 saved states through the package verifier
and separate standalone checker, plus 32 operation traces with independent
hole/score deltas and rollback checks. It found zero covers. `diagnose.py`
independently checked both best records, raw aliases, minima over saved search
states, and initial/improvement/final log scores. Forced preflight moves are
excluded from search-minimum comparisons. No solver proof claim is made.

# Reproduction and provenance

`DESIGN.md` defines the score, pair targets, unchanged legal moves, temperature
scaling, best-state ordering, and restart behavior. `seeds.json` binds the v1.0
best states to the unchanged audited108 catalogs. `environment.json` binds the
source, build flags, compiler, binaries, seed manifest, source revision, and
runner/auditor sources. `verification-sources.json` binds both covering checkers
and the dependency lockfile. `manifest.json` hashes compact evidence and records
the independent gate. All labels are 1-based and saved blocks lexicographic.

Complete binary builds, source snapshots, catalogs, every saved state, damaged
controls and covering-checker output remain under ignored
`experiments/scratch/four-seven-template-native-v1.1.0/`. Native elapsed budgets
exclude catalog loading and forced controls. Main-loop acceptance counters
exclude restart perturbations; their denominator includes invalid proposals.
