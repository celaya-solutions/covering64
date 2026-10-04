```text
Document:    Protected Novelty Followed by Unrestricted Repair
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      aabd5bd1fe3d1d51f7c27a87fbb7714e66ca99f68abc2b501ac390b7472ae5d4
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Protected novelty followed by unrestricted repair

Six authorized runs used exactly 64 distinct blocks, with a total search budget
of 10 seconds each. No run found a cover. Five runs returned to three holes;
B with 32 forced replacements reached only 11 holes during repair. The initial
three-hole state remains the overall best for all six runs.

| Start | Forced replacements | Seed | Forced endpoint holes | Best repair holes | Final holes | Recorded seconds |
|---|---:|---:|---:|---:|---:|---:|
| A | 8 | 2026104901 | 8 | 3 | 12 | 10.0004 |
| A | 16 | 2026104902 | 16 | 3 | 34 | 10.0003 |
| A | 32 | 2026104903 | 32 | 3 | 36 | 10.0004 |
| B | 8 | 2026104904 | 8 | 3 | 12 | 10.0003 |
| B | 16 | 2026104905 | 18 | 3 | 31 | 10.0003 |
| B | 32 | 2026104906 | 33 | 11 | 33 | 10.0003 |

There are 137 saved-state records and 12 distinct three-hole families: starts A
and B plus ten new labeled families. Every one contains all 60 original core
blocks and retains the known forbidden five-heavy profile. The existing
relabeled-core screen also found a mapping for each family; the readback checked
each mapping by direct block containment. Thus none escapes either known
structural obstruction. The readback records exact labeled additions/removals
relative to both starts, degree multisets, triple multiplicity histograms,
original-core overlap, and structure-screen results. New labels here do not
establish new isomorphism classes.

## Method and validation

This is a small implementation of the protected outside-pool diversification
idea described in Dai's 2006 thesis; source details and visually checked pages
are in `../local-search-methods/README.md`. Starts A and B each have three holes;
their intersection has 62 blocks and their union has 66. A forced step chooses a
minimum raw-hole-delta replacement from outside that 66-block union. Incoming
blocks remain protected until all configured forced steps finish. All protection
from that phase is then released. The repair considers the full 4,368-block
universe, using the existing weighted tabu replacement rule, with no automatic
reset. Temporary ordinary tabu tenure still applies during repair.

The old heuristic source was left unchanged and is included by a new separate
source file. Repair aspiration compares raw holes with the best repair score,
unlike the old global-best comparison. Checkpoint, independent recount, and
clock checks also differ from the original loop. The 10-second clock starts
before initial checkpoint and forcing; it includes both phases. Tiny final
checkpoint overhead explains recorded durations just above 10 seconds.

Before optimization, 1,024 deterministic replacement/rollback controls were
checked in native code and by independent Python triple-union recounts. Four
bad native inputs were rejected: duplicate, malformed token, out-of-range label,
and wrong cardinality. Each forced trace was independently replayed, including
exact deltas, 64 distinct blocks, incoming membership outside the elite pool,
and protection of earlier incoming blocks. Every saved state passed the package
and standalone verifiers with matching uncovered triples and canonical hashes.
Native repair also performs a full direct recount every 1,024 steps and at each
saved state; every replacement checks its incremental hole delta.

`readback.py` independently counted coverage by direct subset containment for
all 137 records, checked source/artifact hashes, and rejected 18 damaged result
records. Equal-cost checkpoints capture one distinct labeled family per repair
best level. Forced improvements, including any hypothetical zero-hole family,
are saved before the next forced step. Source, binary, compiler, exact commands,
seeds, budgets, source revision, logs, and all saved families are pinned in the
metadata and case records. The 60-core screen is reused unchanged and hash-bound.

## Artifacts and scope

`metadata.json` pins preparation. `summary.json` and the six case JSON files
record the runs. `readback.json` records independent readback and structure.
Raw snapshots, binary, full JSONL traces, and all families remain under the
Git-ignored `experiments/scratch/forced-novelty-20261004/` directory.

No case was repeated. No restriction used here is claimed complete for all
covers. Positive hole counts are heuristic outcomes, not exclusions or a global
lower bound. This campaign produced no new cover and no impossibility theorem.

Frozen file hashes:

- `forced_novelty_heuristic.cpp`: `52a4437589c1c18c2fb0df2573802520a963a843ec79a198eb1ecf230faaf9c2`
- `campaign.py`: `947c030ea03d749a503710bdc98f607948ff000f3a991c5f093c3d391f8b3d5a`
- `metadata.json`: `24bf8213bb142df299cdacfa72cbded43d88fe78b57b78843c7a578894d2afbc`
- `summary.json`: `6c9324fda9d967e5a1764dee83233298e23f7fc0d0cc603f1f3104c99f591cf8`
- `readback.py`: `c8c92feb1fd3b0159aaa6ba41ea13f9df3d40041ba4a569d374b7135cf41e041`
- `readback.json`: `337f2e5e9b18a842d02398bc9e89503a89427019955530fe1a326f206541d581`
- Native binary: `739a37c8245d4f747152efcd9058fa819511ae8f43c243883707bde2ea6d42dd`
