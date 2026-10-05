```text
Document:    Independent Replay of Affine LP Farkas Certificates
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      fb21157fcac308f8889f3d7d7e44b4f2d4074d0a3a62123b952249b84e49fdba
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent replay of the LP certificates

`check.py` uses no producer import, LP solver or NumPy. It pins the certificate
stream and both survivor streams, requires the certificate stream to list
every input case exactly once, and replays each certificate with integers.

For each case it rebinds the pair ordinal to its partial and profile through
the catalog fibers, rebuilds the twenty-block partial, checks every triple
through point one against its profile multiplicity, recomputes all 455
residual demands, enumerates the kept five-subsets avoiding point one by its own
construction, and recomputes the exact margin. The margin must be positive and
equal the saved value; the kept-column count must match.

All 208,570 certificates pass in about 36 seconds with eight processes. Seven
damaged controls are rejected: a changed multiplier, an overstated margin, an
empty certificate, a wrong profile, a wrong partial, a fractional multiplier and
a changed column count. `review.json` records the checker hash and results.
