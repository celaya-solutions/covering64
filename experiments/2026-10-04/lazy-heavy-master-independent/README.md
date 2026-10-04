```text
Document:    Independent Lazy Heavy Master Review
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      4aee4ee73a6e2ce979ddb502ec61a652a3adbb759db4aa0c828a4e7e2773cdb9
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent lazy heavy master review

The initial master passed a complete protobuf comparison: 276 lexicographic
heavy-block Boolean variables, one cardinality row, 52 outside-degree rows,
552 supported nonanchor triple upper bounds, and 14 independently replayed
cuts. All 619 rows and the absence of extra model fields match. The 697-row
completion basis was reconstructed directly from combinations and compared
with the pinned existing oracle.

The source review confirmed the residual subtraction on both finite bounds,
continuous ordinary variables in [0,1], exact signed-dual arithmetic, and the
cut `heavy_sum >= constant - positive_ordinary_box_max`. The solver is bounded
and fractional feasibility is explicitly distinct from an integer cover.
`check.py` and `audit.json` record this pre-run gate.

After the ten-step pilot, `postcheck.py` independently replayed every incremental
master, selected heavy tuple, solver parameter file, residual LP row, and learned
cut. Every cut separates its source tuple by a positive exact rational gap.
The initial 14 plus ten new cuts are now checked. Each case concerns the regular
four-sevenfold family and a fixed heavy tuple. These checks give no unrestricted
lower bound or global nonexistence result, and do not rely on CP status as a
proof. No optimization was run by either checker. Scoped Ruff checks passed.

Raw pilot evidence remains in its original ignored scratch directory. The
independent receipts bind every consumed source, model, witness, and certificate.
