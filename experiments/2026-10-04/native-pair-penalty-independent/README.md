```text
Document:    Independent Native Pair-Penalty Gate and Outcome
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      d32979557da6c6161b57adcfa1a3650d33b0eab8a88936e2cd5a3c1f5b44ddce
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent native pair-penalty checks

The gate binds the frozen native source, binary, runner and two sixty-second budgets. The old core implementation and universe source are byte-identical to the already audited core-cap version. The new affected-pair update includes every pair in the old/new block union, including shared pairs whose count does not change.

Independent sanitizer controls reconstruct all pair, triple and quadruple counts directly from block masks. They check 901 full recounts, 360 accepted transitions, 337 rollbacks, three duplicate proposals and forty cases of each old/new intersection size zero through four. AddressSanitizer and UndefinedBehaviorSanitizer pass. Uniform draws are consumed on every proposal in this version, so its seeded trajectory is not the old version's trajectory.

Postcheck replays every saved and final role: 21 records representing twelve distinct families, with 24 fresh covering-verifier calls. The raw and score bests keep six holes and four single-triple deficits. A separate zero-deficit record reaches 48 holes for seed 2026104401 and 49 for seed 2026104402. Both have pair minimum five and no forbidden profile; they remain incomplete. Final current states and ties are kept separately. No cover is found.

The paired local inequalities used by this native search are weaker than the newly prepared two-triple rows. These records are not claimed feasible for that stronger compact model. The producer's separate post-relabel screen certifies both zero-deficit finals avoid every relabeling of the original core trap. The six-hole start has a newly checked 59-overlap fourth core; these frozen runs retained only the original three named caps.

Run `check.py` and `postcheck.py` from this directory with `uv run python` for replay. The independent C++ control is built with C++20, optimization O1, debug information, AddressSanitizer, UndefinedBehaviorSanitizer and frame pointers. Frozen optimizer binaries, sanitizer binaries and raw logs remain in ignored scratch.
