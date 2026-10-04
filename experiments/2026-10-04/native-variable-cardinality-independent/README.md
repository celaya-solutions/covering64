```
Document:    Independent Native Variable Cardinality Gate
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      2d16bc0b5494fb9c93bb60381b230cecde5278785b8720b90f827efd3f2c06fe
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent native variable-cardinality gate

Decision: GO for the exact frozen implementation and declared bounded campaign.
Only root may launch it. This audit launched no optimizer and changed no producer
source. The gate file is frozen and must not be overwritten.

- Producer manifest: `../native-variable-cardinality/manifest.json`, SHA256
  `f79075467ba41b46e53491c032044a23fe9766c680309055c1ff5d0697ec354b`.
- Gate: `gate.json`, SHA256
  `300677f074664d001cba3c63cb156e13e2648020cfa28908560b5f761ad3c6ff`.

## Independent checks

The oracle builds every 3-subset and 5-subset from16-bit masks, sorts by point
labels, and tests subset inclusion directly. It imports no producer score,
count, adjacency, weight, or move-update calculation. It compares the resulting
universe,78 carriers per triple,10 triples per block, and every state field
against the frozen kernel. Graft does not index C++; source reads were targeted.

ASan and UBSan controls passed213 complete state snapshots and930,384 block
score/pscore comparisons. All counts, weights, cardinality, holes, choices, CC
flags, and last-flip timestamps were independently checked at each snapshot.
Incoming selection was checked500 times, including all100 residue values across
age/fallback scenarios. The quantized novelty test selects the second best for
11 residues, consistent with `(random()%100)/(double)101 <0.1`.

Eleven invalid-operation controls reject duplicate or invalid initial IDs,
already-selected additions, absent removals, invalid IDs/score requests,
invalid incoming inputs, covered targets, and empty-family removal. The score
ordering includes the declared global-lex final tie-break. Controlled primitives
exercise65->64->63->64->65 and a deliberate66-block state to show there is no
64-block restriction in the kernel. These primitive controls are distinct from
the actual trajectory's strict incumbent-size policy.

Bounded deterministic transitions exercise complete drop, add-only, swap, and
sequential double-drop branches. The second outgoing choice is recomputed after
the first removal. Every observer event is checked before any later mutation;
an observer-requested stop prevents later changes and weight increments. Weight
updates occur only for uncovered triples after an unfinished add-only step.
There is no decay. The complete-target predicate is holes==0 and cardinality<=64.
Its scalar unit controls are explicitly synthetic metadata, not covering witnesses.

Six file controls reject duplicate blocks, out-of-range/damaged labels, malformed
block size, a truncated baseline, repeated within-block labels, and a65-block
family with damaged coverage. Four saved control families are independently
recounted and checked by both the package and standalone covering verifiers.
The baseline has65 distinct blocks,560 covered triples, and650 incidences.
Partial control states are recorded at their actual cardinalities, without
being mislabeled as covers.

All29 producer source/input/raw artifact hashes and the compiler hash were
checked. `build.json` records the independent compiler, exact flags, source and
binary hashes, deterministic mutation seed, and successful sanitizer control run.
The independent raw directory contains the compiled control, finite logs, and
saved/rejected witnesses; it stays outside Git.

## Driver review and boundaries

A separate agent reviewed the exact frozen search.cpp and run.py hashes bound
in the gate. No blocking issue was found. The observer saves records after each
primitive and stops immediately on a verified cover of at most64 blocks. The
actual final state and every present best record are saved; missing64-block
records are explicit nulls. The Python runner dual-verifies actual cardinality,
checks final status, and stops the campaign on the first verified target or error.

Deadline checks occur between advance iterations. At most two primitive mutations
and audit/save cleanup can complete after the native deadline; the runner records
actual elapsed time and applies the declared watchdog. The authorized manifest
allows at most two sequential120-second runs with seeds2026104701 and2026104702,
with no relaunch or reassignment of unused budget.

Core caps are diagnostics only and never filter the trajectory. The admissible64
label checks four named core caps only at exactly64 blocks; it is not a global
relabel screen. No64-specific cap is imposed at other cardinalities.

This is an independently written implementation of the source-described unit-cost
NuSC rules, with explicit deterministic tie handling. The upstream reference is
[NuSC commit fdacd80](https://github.com/chuanluocs/NuSC-Algorithm/commit/fdacd80d92e7143b4fe305bddce471a1e8982e90).
No upstream implementation was compiled or linked by this audit. The prior
producer manifest is preserved, but pre-format Python source bytes were not
separately retained; the current audited source bytes are fully hash-bound.

Finite controls and source review do not prove search quality, existence, or a
lower bound. No actual<=64 cover was available during the audit, so that success
path was reviewed structurally and through immediate-stop/predicate controls.
No discovery or independent nonexistence theorem is claimed.
