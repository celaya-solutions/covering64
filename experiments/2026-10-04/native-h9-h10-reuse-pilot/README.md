```text
Document:    H9 H10 Native Reuse Pilot
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      0775edf256040665cced20e9c50c65e7f647ccf32b44983276b7c6a55feaa188
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Fresh starts, unchanged native search

This pilot reuses the exact frozen native binary and Python driver from the
completed five-core record pilot. It does not rebuild or edit them. The new
wrapper changes only output locations and the seed list before delegating to
the old driver. The native walk, weights, random draws, initial eligible-state
fallback, cardinality changes, and all record buckets remain unchanged.

| Seed | Start hash prefix | Holes | D2max | D2sum | Sixth overlap |
| --- | --- | ---: | ---: | ---: | ---: |
| 2026105901 | a0a737c4010f68fc | 9 | 19 | 27 | 59 |
| 2026105902 | 85f6e38a53769144 | 10 | 22 | 32 | 0 |

Both starts pass the unchanged five named caps, pair floor five, D3 = D4 = 0,
and the separately proved sixth named cap59. Both therefore initialize the
raw64, five-cap-admissible64, and weak64 record buckets. The ordinary 65-block
complete incumbent initializes the separate complete bucket. All initial
weights, timestamps, scores, and fallback behavior retain the frozen driver's
semantics. The retained eligible initial state is never replaced with an
unqualified fallback.

There are at most two sequential 300-second calls, with a 315-second watchdog
and five-second termination grace each. Seeds are fresh, and no time is moved
between calls. A real complete family of at most 64 blocks stops the entire
campaign immediately, regardless of cap or weak-record qualification. Every
saved family is checked by the original package and standalone verifiers.
An incomplete, invalid, interrupted, or watchdog outcome cannot be a covering
claim. Root owns the sole production launch after independent GO.

# What the sixth cap does

The independently checked radius-four certificate proves that every exact
64-block cover overlaps the named f5f24 family in at most 59 blocks. The new
wrapper binds that proof and its independent receipt. It applies the sixth
cap only after the unchanged driver finishes, and writes a separate
`saved-six-cap-classification.json` receipt. The driver's `result.json` and all
native witnesses remain unchanged.

Both independently qualified input witnesses remain explicit eligible
fallbacks in the classification receipt, including the second input if an
early cover stops the campaign before its launch. Such an unlaunched input is
identified separately and is not counted as a native saved reference.

The classifier checks every saved record and final reference, reports the
sixth overlap, and identifies the best saved family satisfying all six named
caps and the existing weak rules. Its rank is `(holes,D2max)`, with full block
IDs as a deterministic tie break; D2sum is metadata. The sixth cap applies
only to exact64 families. It never restricts live moves, changes recording,
or disables the unconditional complete-cover bucket and stop.

This does **not** identify the best six-cap state ever visited by the walk.
The unchanged driver might discard such a state because it did not improve
one of its five-cap record buckets. The certificate applies to a fixed named
family; passing six named caps is not escape from every relabeling. The old
driver also retains its explicitly scoped historical comparison against the
old 205-family inventory. That baseline is not the current H9/D19 frontier.
The new start and saved-six-cap comparisons are separate and explicit.

# Controls and preservation

Preparation checks all inherited binary, source, input, and proof hashes. It
uses the already built sanitizer control binaries for exactly zero and eight
steps from each new input/seed, exercising the unchanged driver and parser.
Both eligible starts must remain present in all initial eligible buckets; the
eight-step controls retain four initial fallback steps and reach cardinality
62. These four bounded control calls are not timed optimization calls. No
kernel, driver, recorder, or input artifact is altered or rebuilt.

The manifest pins the new wrapper/preparer, control receipts, both starts,
budgets, old driver and binary, completed source campaigns, old core rules,
sixth-cap producer certificate, and independent cap audit. The wrapper needs
`--gate PATH --gate-sha256 SHA --execute`, checks an independent hash-bound GO,
and inherits the driver's refusal to launch over existing output. No relaunch
or budget transfer is authorized.
