```text
Document:    Independent Sole Degree Nineteen Model and Primal Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      3fe33a96b4929b44ed1ff9765d205172ab443c200f030e3afbd8ddc46aa974b6
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent sole-degree-19 audit

`check_models.py` reconstructs every constraint in all 38 raw protobuf models without importing the model builder. All models passed. All 18 damaged model and inventory controls were rejected.

Each model has 4,368 Boolean variables in global lexicographic five-block order and 2,062 linear rows: 560 triple coverage rows, cardinality 64, 16 exact degree rows, 120 pair lower bounds of five, and 1,365 point-1 variable fixes selecting the frozen 19-block link. Point 1 has degree 19, one specified point has degree 21 and the remaining 14 points have degree 20. Classification and distinguished-point orbit completeness were audited separately in the roadmap work.

`replay_primals.py` reads the 38 stored 4,368-entry LP primal vectors and the raw protobuf models. Each IEEE754 value is converted with `as_integer_ratio()`, scaled to a common power-of-two denominator, and all row and variable-bound residuals are recomputed using integers. All residuals are within 1e-7. The largest exact binary row residual is approximately 3.6502745270894366e-13; variable-bound residuals are zero. None of the stored vectors is exactly feasible, and every vector is fractional. Nine damaged primal or inventory controls were rejected, including malformed lengths, nonfinite/Boolean values, bounds, a broken fixed block, and missing/duplicate cases.

These checks validate model construction and numerical LP readback. They produce neither integer covering witnesses nor exclusion proofs. Reports are `model-audit.json` and `primal-replay.json`; raw model and primal inputs remain under ignored `experiments/scratch/`. See `manifest.json` for full-file hashes.
