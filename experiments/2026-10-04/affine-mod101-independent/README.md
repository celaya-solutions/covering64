```text
Document:    Independent Prime-101 Certificate Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      c419641f9220190fba70a091bff912b67d1c24f339bbfc6f8b2742eed49b4ca2
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent prime-101 audit

`check.py` replays all 32 saved outcomes of `../affine-mod101-benchmark/`
without importing the producer or NumPy. It pins the producer's result,
manifest, plan and source, and every manifest input. Each case is rebuilt from
the frozen catalogs: twenty fixed point-one blocks, the eighty excess triples
of its profile, residual demands `1 + e_t - l_t` on the 455 triples avoiding
point one, and the sum-44 row. Columns meeting a zero-demand triple are dropped,
and the saved zero rows and eligible block IDs must match exactly.

For the four contradictions the checker confirms `yA = 0` on every kept column
and `yb` equal to the saved nonzero residue modulo 101. For the 28 consistent
cases it confirms `Ax = b` modulo 101. Every case must come from the 616-case
parity-consistent pool of `../affine-mod2-pilot/result.json`.

Result: 4 contradictions and 28 field-consistent systems, matching the
producer. Eight damaged controls are rejected: a changed multiplier, a zero
certificate, a wrong residue, a changed demand on a used row, a restored dropped
column, a changed solution value, a truncated solution and a negative value.

The four excluded cases are expanded pair 1,266,773 and original pairs 54,692,
4,949 and 99,638. A field solution is only a necessary condition. These are
exclusions of those fixed link/profile completions, not of general covers.
