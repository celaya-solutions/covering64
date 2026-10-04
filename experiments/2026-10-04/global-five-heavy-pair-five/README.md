```
Document:    Prepared Global Five-Heavy DP Model with Elementary Pair Floors
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      e931e8724f1ad177c1f91d5298d4fff7ff046ee37781d1eaac2ca7b1a698d70c
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Prepared global five-heavy model with pair floors

Preparation and runner readback passed. Optimization has not run. The independent
gate is pending. The frozen model has 10,488 variables and 103,465 rows.

The preparation source loads the earlier frozen global five-heavy DP model,
keeps every variable, all 103,345 prior rows, and its objective unchanged, then
appends exactly 120 pair-floor rows. Global block IDs remain zero-based
lexicographic IDs and all point labels remain one-based. Each new row sums the
364 block variables containing its pair and requires that sum to be at least 5.
The three core caps, named partition rows, and global DP encoding are unchanged.

## Why the new rows preserve every full cover

Fix any pair P. Fourteen triples contain P. A five-block containing P covers
exactly three of those triples, while a block not containing P covers none.
Therefore 3 c(P) >= 14 in any full cover and the integer count satisfies
c(P) >= ceiling(14/3) = 5. This proof does not assume regular point degrees,
incumbent incidence, a construction family, or symmetry. The new rows can remove
near-covers while preserving every valid 64-block cover.

`pair-rows.json` lists all 120 pairs in lexicographic order, all supporting
block IDs, and their appended row IDs 103345 through 103464. Independent review
can compare the complete parent prefix, append these exact rows, and recount
the new complete hint without invoking an optimizer.

## Checked hint

The bounded audited inventory selected an existing six-hole state, SHA256
`797dada195b23eecc808798eb12c8e4e7ccd7edd026fbdf22dea5b341f9ea2de`.
It has core overlaps [2, 2, 0], minimum pair count 5, and maximum global partition
weight 22. The objective is 392 = 65 × 6 holes + 2 original-core overlap. Both
covering verifiers freshly checked the candidate during the inventory.

The preparation independently rebuilds all 10,488 hint values from the blocks:
4,368 block indicators, 560 exact hole indicators, 30 retained named thresholds,
1,120 exact global thresholds, and 4,410 least DP values. It checks every variable
domain and every active row, including the new pair rows. Full point degrees,
pair counts, triple multiplicities, and histograms are in `hint-diagnostics.json`.
The regular degree-20 profile is a property of this hint, not a model constraint.
Passing these filters does not imply the hint is a cover or passes every known
necessary condition.

## Frozen artifacts

| Artifact | Path or SHA256 |
| --- | --- |
| Preparation source | `prepare.py`; `a6c97a430e57737bb4c682138e2f8fedb923248a314533428dc0778a5b47a626` |
| Preparation manifest | `manifest.json`; `734ce1904211c4af6b25927885143b0a3669461e5ceb5e0d02e07636e47f855c` |
| Model | `experiments/scratch/global-five-heavy-pair-five-20261004/full-4368-model.pbtxt` |
| Model hash | `7c40dea304362e250002ac93d9995630e9822bc5c25fa1435ba5cf1ae1716f79` |
| Parameters | same scratch folder, `parameters.pbtxt`; `dd407e9b2b9b5467bfc45426162270489e7001d61797d072bb0ba7666018cca9` |
| Runner | `execute.py`; `7fe86396f79217223c02962cfb0f16789bee3911c366b9125d0ec12974ebb4b8` |
| Readback receipt | `runner-preflight.json` |
| Local artifact hash index | `files.json` |

The preparation scratch folder also preserves the full hint vector, the exact
candidate text, every source/input snapshot under `frozen-inputs`, and a separate
frozen runner copy. The 29,934,852-byte model and other raw artifacts stay ignored.
`build-stats.json` records preparation-only timing and process memory; it makes
no solver propagation or performance claim.

The saved parameters specify one run of 120 seconds, four workers, and seed
2026104105. The runner requires a passed gate binding `manifest_sha256`,
`source_sha256` (preparation), `runner_source_sha256`, `model_sha256`, and
`parameters_sha256`. It reads the saved model and performs one solve only after
that gate; it cannot rebuild the model or overwrite an existing run directory.

The runner retains the earlier recording policy: every callback improvement,
distinct best-score tie, and final native response with all variable values,
plus logs, sources, parameters, and hashes. It recounts pair floors, core overlaps,
holes, and the actual global partition maximum for each saved state. A zero-hole
callback stops the run, and a covering witness must pass both covering verifiers.
Near-covers still require a separate postcheck. A timeout is inconclusive; a
native infeasibility status is not an independently checked global theorem.
