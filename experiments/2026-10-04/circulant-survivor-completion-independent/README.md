```text
Document:    Held Circulant Survivor Completion Gate
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      c8f264780f538291ecf6a04d38812e4df68d9a93050b58a587739207a5aeb6da
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Held conditional-completion gate

The four frozen models pass independent encoding, selection, and launch-control
checks. The gate is HOLD with zero calls authorized because root deferred this
batch after a new parity pilot reported contradictions for three selected cases.
The model review remains useful evidence, but it does not authorize a launch.

All four models exactly match independently constructed protobufs: all 4,368
lexicographic Boolean block variables, 560 exact triple-demand rows, one exact
64-block row, and 1,365 point-one membership rows. Exactly twenty of those
memberships are selected. The remaining 3,003 block variables retain their full
Boolean domains. There are no objectives, hints, search strategies, extra
propagation pins, cover-invariance restrictions, or missing equations.

The independent selection replay checked all 1,096 input cases and all 548
two-case reflection orbits. The class census is 410 C4-leaf, 658 triangle-path2,
and 28 triangle-two-leaves. Taking the minimum free-count/pair-ordinal pair per
sorted class, then the minimum eligible case from a new profile orbit, gives
pair ordinals 55433, 48366, 51739, and 135193. Their reported free counts are
325, 308, 378, and 321; the four profile orbits differ. These counts select cases
only and impose no model restrictions.

Both verifiers independently checked all four pinned twenty-block partials,
with 185 covered triples and 375 holes. All residual demands were reconstructed
and checked, including the 105 equations containing point one and the 455
outside equations summing to 440.

All 72 damaged model/parameter controls were rejected. Ten mocked controls
passed: five watchdog paths, three four-call wrappers including pin changes
and a killed child, and two workers preserving UNKNOWN/INFEASIBLE status without
claiming a cover or independent infeasibility proof. The planned calls would
have used 30 seconds and one worker each, seeds 2026106701 through 2026106704,
and a 35-second watchdog plus five-second grace. No real solve, process, or
signal occurred during this audit. All 21 input pins and 25 prepared-file pins
match; Ruff passes.

A passing encoding audit does not prove these cases feasible or infeasible.
The models are conditional on each chosen partial and fixed profile; they do
not exhaust surviving cases or establish a global covering lower bound.

```sh
uv run python experiments/2026-10-04/circulant-survivor-completion-independent/check.py
uv run ruff check experiments/2026-10-04/circulant-survivor-completion-independent
```
