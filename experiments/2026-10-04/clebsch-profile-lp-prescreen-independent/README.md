```
Document:    Clebsch Profile LP Independent Vector Replay
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      26d78cfc2a0c8c285d0fd1c7b0a8caaba000bde0cbf7682592d78ce3ea6e79d6
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent replay of the sixteen fractional LP vectors

All 16 saved vectors pass a numerical replay from all 4,368 lexicographic blocks.
No optimizer was invoked. The checker also replays the existing orbit certificate:
1,024 recipe profiles, 80 point actions, 16 disjoint orbits, and every saved seed
normalizer. The source, generator, certificate, seed order, and vector hashes match.

Each vector has 560 positive fractional coefficients and 3,808 exact zeros. None
has a coefficient near one, and none is an integral block-family witness. The
reported 3,808 integral columns are the zero coefficients, not selected blocks.

| Recomputed quantity | Largest absolute residual |
| --- | --- |
| 560 exact triple demands | 1.96698213272839e-12 |
| 120 pair demands | 1.899813639738568e-12 |
| 16 point demands | 2.284394895468722e-12 |
| Sum of coefficients, target 64 | 1.7337242752546445e-12 |
| Bounds [0,1] | 0 |

For each recipe, 80 triples have demand two and 480 have demand one. Summing all
triple rows gives 640 incidences, or total coefficient weight 64 because a block
contains ten triples. A pair's demand is one-third of the demands of its 14
containing triples; this gives 80 pair demands of five and 40 of six. A point's
demand is one-sixth of its 105 containing-triple demands, giving 20 at every point.
The independent replay checks those pair and point sums directly from the vector.

The replay uses stable floating-point summation and a declared 1e-8 numerical
feasibility tolerance. It agrees with the producer's reported counts and residuals.
Eight damaged vectors were rejected, covering shape, type, nonfinite values,
bounds, all-zero data, and a perturbed positive coefficient.

These are feasible fractional relaxations within numerical tolerance. They do
not provide a binary cover, exact rational certificate, or unrestricted existence
conclusion. The recipe-orbit certificate has its own limited scope and does not
classify all possible excess profiles or all covers.

Reproduce with `uv run python experiments/2026-10-04/clebsch-profile-lp-prescreen-independent/check.py`
in a checkout with the current receipt preserved elsewhere. The checker refuses
to overwrite its receipt. Ruff passes. Full hashes are in `review.json` and
`files.json`.
