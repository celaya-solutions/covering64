```
Document:    Independent Native Partial-Start Gate
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      b4b20726233ee6a7670d03f487f72e3bfd5e77535072a32f7c2d01d403af66f6
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent partial-start gate

Decision: GO for the exact frozen variant and declared two-run budget. Only the
parent agent may launch the campaign. This audit launched no timed optimizer.
The gate and the source bytes it binds are frozen.

- Producer manifest: `../native-variable-partial-start/manifest.json`, SHA256
  `d66e4f2dfe7604b06dcd9d94ac49efc0c82b748b03977195e4a3924f6b2daaa5`.
- Gate: `gate.json`, SHA256
  `ea66aee6e55730dc8b0716e0472badc64cabed1b58468d25ba23293d9d8158d5`.

## Scope and reused evidence

The kernel and four-core data are byte-identical to the previously audited
native variable-cardinality variant. This audit binds its frozen kernel gate,
SHA256 `300677f074664d001cba3c63cb156e13e2648020cfa28908560b5f761ad3c6ff`.
The unchanged kernel checks were reused rather than repeated. That earlier gate
records 930,384 independent score comparisons and finite transition controls;
it is not a mathematical proof of a search result.

This gate independently checks the new constructors, partial-start records,
cardinality accounting, input roles, manifest, and runner budget. A separate
agent reviewed the exact changed driver and runner and reported no blocking
issue. All producer source, input, and raw-file bindings passed.

## Independent controls

Each run keeps the verified complete Belic65 incumbent separate from its
incomplete 64-block live state. The first authorized seed is 2026104801, with H9
and core overlaps [1,0,0,0]. The second is 2026104802, with H12 and core overlaps
[1,1,1,2]. The independent constructor program confirms unit weights, enabled
CC flags, zero last-flip timestamps, age eligibility, fresh triple counts, and
separate state storage. It performs 21,840 age checks for each start and verifies
that changes to the live state leave the incumbent unchanged.

The actual frozen driver was compiled independently with ASan and UBSan, once
with a zero-step limit and once with an eight-step limit. Both starts passed
both limits. Zero-step controls saved complete, raw64, and admissible64 records
at step zero with zero mutations. The initial live minimum and maximum were
both 64; the separate 65-block incumbent did not affect that range.

Each eight-step run made 14 primitive mutations, with live minimum 62 and
maximum 64. The first four steps used the required age fallback. An independent
Python replay checked the explicit removals and additions, first-lex fallback
carrier, cardinalities, coverage, weight increments, counters, and final state.
All 31 saved-family checks passed both the package verifier and the separate
standalone verifier at their actual cardinalities. These are 31 checks, not 31
distinct families. Wrong input roles and a wrong budget were rejected by the
zero-step binary. Sanitizer stderr was empty.

`build.json` records compiler identity, flags, source and binary hashes, and the
raw artifact index. `files.json` binds the small committed audit files. Binaries,
logs, and saved control states live under the ignored scratch directory.

## Authorized budget and limits

The manifest permits exactly the declared sequence of at most two 300-second
runs, with seeds 2026104801 and 2026104802 and no simultaneous runs. The watchdog
is 315 seconds with a 5-second termination grace. There is no relaunch and no
reallocation of unused budget. The campaign stops at the first verified cover
of at most 64 blocks or at an error. Fixed-step controls do not consume this
search budget.

Every relevant state is considered and saved before the target predicate can
stop the search. Coverage requires zero holes; incomplete 64-block records are
not covers. Four-core admissibility is a diagnostic at cardinality 64 only, not
a restriction on the trajectory or a global relabel test. The finite controls
do not establish existence, nonexistence, or a global lower bound.
