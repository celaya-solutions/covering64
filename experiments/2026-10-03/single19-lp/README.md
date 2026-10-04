```text
Document:    Sole Degree Nineteen LP Screen
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      a5b2737eb94e8b6b4f7404ce895b4c195be4c0d04968c754d96c87cf449373d8
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Sole-degree-19 LP screen

All 38 roadmap cases returned GLOP OPTIMAL with numerically feasible, fractional solutions. No integer cover, infeasibility certificate, or excluded case was obtained.

Each case used one thread and a total 15-second wall budget, including any potential phase-I certificate attempt. The 38 measured case times totalled 6.576529584941454 seconds; the largest was 0.27276916697155684 seconds. Five certificate arithmetic controls passed before launch. No certificate was needed or generated.

The original runner completed and saved all 38 solves, per-case records and 4,368-entry primal vectors. Its final summary writer then failed because it applied `relative_to(absolute ROOT)` to a relative output path. `finalize.py` checked the intact inventory, per-case result equality and primal hashes and wrote the summary. No solve was repeated. The frozen executed runner is retained unchanged; future use must provide an absolute output path until a separately versioned correction is made.

`summary.json` and `results.json.gz` are the compact retained result. The ignored archive `experiments/scratch/single19-lp-v1.0.0/` contains the executed source, environment metadata, raw models, row archives, logs and primals. `../single19-independent/` reconstructs the models independently and reads the stored binary floating-point values back with exact integer arithmetic. All residuals are within 1e-7, but none of the saved vectors is exactly feasible; the largest exact binary row residual is approximately 3.6502745270894366e-13. These results describe only the LP relaxation.

See `manifest.json` for full-file hashes. Header SHA256 values hash only the content after each header.
