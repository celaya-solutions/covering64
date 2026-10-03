```
Document:    Independent Exact Rational Witness Recounts
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      067a17ac7f9d58526f250c0c8f77919e0a58e3d0ef80a186a3ab1874baff42a9
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Exact fractional witnesses

`lp_check.py` uses only Python's standard library and exact Fractions. It reads
sparse weights indexed by the full lexicographic 4,368-block list, then recounts
all point, pair, and triple totals directly from raw subsets. It does not load a
solver or inspect the production model as its oracle.

Both original cycle and matching LP vectors pass all variable bounds, total
block weight 64, point degree 20, the 120 pair targets, four sevenfold counts,
and coverage of all 560 triples. They also pass all 156 fixed two-anchor triple
counts. Subtracting one from each eligible triple multiplicity gives a fractional
400-triple vector of total weight 44 that meets all triangle-pair demands.
Neither the block vector nor the double-triple vector is integral.

This establishes consistency of these necessary counting equations over the
rationals. It gives no integer covering witness. The fixed-count property was
checked explicitly; it does not follow automatically from arbitrary fractional
feasibility of the original model, since integral repeated-hub arguments can
fail under fractional weights.

Reports `cycle-lp-report.json` and `matching-lp-report.json` record the nonzero
double weights and four rejected controls each: wrong weight, missing block,
wrong branch, and duplicate variable index. Reproduce with:

```sh
python3 experiments/2026-10-03/four-seven-independent/lp_check.py WITNESS.json REPORT.json
```
