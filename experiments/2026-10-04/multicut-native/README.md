```
Document:    Fourteen-Cut Native Guidance Preparation
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      3493e1ec22511840f04e1b2707395f505d56f8ef659958031dd60693d3838e58
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Fourteen-cut native guidance preparation

The separate source `scripts/four_seven_template_multicut_heuristic.cpp` adds an
optional score guide from the independently checked fourteen-cut bundle. The
single-cut and original lookahead sources are unchanged. No search pilot has
been launched by this preparation.

## Score and runtime interface

The guide is off by default. With `--cut-guide`, its penalty is
`cut_weight * max_i ceil(max(0, rhs_i - lhs_i) / 1000)`. Every cut in this
bundle has denominator 1000. `--cut-weight N` accepts integers from 1 through
1000 and defaults to 1. Setting a weight does not enable the guide by itself.
A weight of 10 is available for a separately authorized pilot.

Fourteen heavy sums are precomputed for every catalog template. A heavy-template
move subtracts the old template vector and adds the new one. Ordinary moves
leave the vector unchanged. The original score terms, legal move definitions,
move generator, cache behavior, and unconditional acceptance of a zero-hole
proposal are preserved. The guide changes only the score while enabled.
All fourteen LHS values, RHS values, violations, the largest violation, the
weight, and the weighted penalty appear in saved lookahead sidecars.

For the fixed bundle and any 28 selected heavy blocks, a conservative bound on
the largest possible violation is 292,828. At maximum weight 1000 the guide
penalty is at most 293,000, safely within the native signed-integer score range.
The guide is a heuristic preference and supplies no new state rejection or
mathematical infeasibility claim.

## Source and build bindings

`prepare.py` binds the original native source, the fourteen-cut bundle, and the
root independent bundle audit before creating the new source. It refuses to
overwrite an existing source or preparation receipt. `preparation.json` records
these inputs and source hashes.

`build.json` records Apple clang 21.0.0, exact flags and binary hashes. The
optimized build uses C++17, `-O2 -Wall -Wextra -Werror`; the diagnostic build uses
`-O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer` with the same
warnings. Both compiled without warnings. A frozen original lookahead binary
is used only for disabled-guide control comparisons. Binaries, source snapshot,
full native diff, build logs, large catalog outputs and control state files
remain outside Git in `experiments/scratch/multicut-native-v1.4.0/`.

The root separately inspected the native diff and replayed all 276 embedded
masks, 3,864 coefficients, fourteen RHS values and the bundle hash. Its receipt
is `../multicut-native-root/audit.json`.

## Focused runtime audit

`audit.py` independently recomputes scores and full lookahead sets using the
previous Python oracle and the JSON cut bundle. It covers both catalog types,
all four native move modes, rollback, rejected-move nonmutation, the disabled
guide and weights 1, 10 and 1000 in both optimized and sanitizer builds.
The default enabled weight is separately checked as 1.

The audit passed:

- 148,248 unique catalog templates, each with fourteen exact sums, in both
  builds: 4,150,944 sum comparisons.
- 286 saved states and 88 applied moves. All ten distinct saved state contents
  passed both package and standalone cover/hole-count validation; they are
  near-cover controls, not claimed covers.
- Exact default-off forced trajectories match the original lookahead binary
  at weights 1 and 10, for both builds and both catalogs.
- Fifteen damaged sidecar fields and sixteen invalid CLI argument controls
  were rejected.
- Ceiling cases -1, 0, 1, 999, 1000 and 1001 were checked for each of the
  fourteen cuts. The zero-hole score override remained active.
- Every valid control run had empty stderr; sanitizers reported no errors.

See `audit.json` for source, bundle, oracle and binary bindings plus every saved
state hash. The native control paths finish before entering the optimization
loop. This preparation does not modify the official 109 first-link exclusions,
the 149 open representatives, or the best verified cover of size 65.

## Reproduction and boundaries

The narrow Ruff check passed. Source generation and runtime audit both require
fresh outputs; use a new version directory for a new preparation. The existing
frozen receipts should be inspected rather than overwritten. Repository-wide
checks and Git integration are owned by the coordinating agent. Any pilot is a
separate, bounded experiment requiring its own recorded seed, budget, source
and binary hashes, logs, saved states and independent audit.
