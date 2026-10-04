```text
Document:    Complete Heavy Template Native Pilot Report
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      a844e351e8e6f86e2a7fd0cdf979686540dc148e8105b6539599620991c712e4
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Whole-template native pilot results

Both 300-second pilots completed normally. No cover was found.

| Catalog | Initial holes | Best holes | Pair-target L1 defect | Largest nonheavy triple count | Proposals |
|---|---:|---:|---:|---:|---:|
| Matching | 62 | 21 | 30 | 3 | 218,376,792 |
| Cycle | 60 | 19 | 24 | 3 | 209,182,374 |

The matching best has four nonheavy triples with count above two; the cycle best has three. These are exact diagnostic recounts, not score terms in this version. Native v1.0.0 minimizes missing triples only. It preserves 64 distinct blocks and degree twenty, using four7-block templates plus36 ordinary blocks. The source, degrees and move rules were unchanged during these runs. Pair targets were not hard restrictions, so the scope is a construction heuristic using branch-derived catalogs, not exhaustive matching/cycle branch membership.

All 144 saved pilot states passed independent catalog/degree recounts and both covering verifiers. All 32 forced or sampled operation descriptors and rollback states passed. Complete pair vectors and verifier-output hashes are in `pilot-audit.json`. The two sanitizer smokes passed without diagnostics, and their84 snapshots/14 moves passed the same checks. Seventeen damaged seed/catalog/argument controls were rejected. Six forced ordinary moves broke the seed rotation, confirming it is not a search restriction. The independent gate separately rebuilt the exact source, checked the complete catalog packs, recounted states and rejected fresh controls before launch.

| Main-loop move | Matching accepted / attempted | Cycle accepted / attempted |
|---|---:|---:|
| Directed two-block swap | 2.0313% | 2.0357% |
| Symmetric-difference redistribution | 1.0689% | 1.0719% |
| Point cycle across3–6 ordinary blocks | 0.0741% | 0.0749% |
| Whole7-block template replacement | 1.7962% | 1.7540% |

The denominator includes invalid proposals. Restart perturbations are separate from these counters. Each process used one thread; at most two ran concurrently. Detailed counts, seeds, timings and hashes are in `results.json`, `summary.json` and `diagnostics.json`. `diagnose.py` independently rebuilds the pair targets and compares each best state with its verifier audit. Four fixed anchor triples are excluded from the nonheavy-triple statistic.

`DESIGN.md` records the state, moves and guaranteed orbit-seed construction. The source is `scripts/four_seven_template_heuristic.cpp`; complete audited108 catalogs contain12,042 matching or25,020 cycle templates per group. `environment.json` freezes source/compiler/binary hashes. `provenance-notes.json` records the header-only seed-constructor hash finalization and auditor v1.0.1 histogram correction; all84 original smoke histograms already contained all120 pairs. No solver or native run was repeated for those reporting changes.

All raw states, complete covering-checker stdout/stderr, source snapshots, catalog packs, binaries and damaged inputs stay in ignored `experiments/scratch/four-seven-template-native-v1.0.0/`. Best witnesses and native logs are retained here. The archived manifest hashes every raw file. The independent launch gate is `../four-seven-template-native-independent/audit.json`. Full-file hashes are in `manifest.json`; this header hashes only the body. Failure of these bounded searches proves no impossibility.
