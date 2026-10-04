```text
Document:    Whole-Template-Hull First-Link Screen Results
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      e6394713714aaed7f5317264375fbb7c170afdbc93f192c36bb72a6d961fa496
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Full-template-hull screen results

All 156 selected representatives finished: 102 cycle models and 54 matching
models. There were 153 numerical OPTIMAL results, three INFEASIBLE results with
independently replayed positive certificates, no unknowns or timeouts, and no
near-integral block candidates. The solver used 815.112990 seconds in total;
the largest per-representative total was 12.507852 seconds, below the
15-second solver budget.

| Case | Screened | Numerical OPTIMAL | Replayed exclusions |
| --- | ---: | ---: | ---: |
| Cycle | 102 | 102 | 0 |
| Matching | 54 | 51 | 3 |

## Independently checked certificates

| Representative | Positive exact gap | Rows | Unit-box variables |
| --- | ---: | ---: | ---: |
| `matching-017` | 1193423/1000000000 | 4,557 | 61,576 |
| `matching-077` | 161/1000000 | 4,557 | 61,576 |
| `matching-083` | 19029/1000000 | 4,557 | 61,576 |

For each row-combination certificate, the independent checker recomputed the
combined lower bound and the maximum over all 61,576 variables in `[0,1]` using
integer arithmetic. It checked the exact seven fixed block rows and rejected
eight damaged controls. The arithmetic reports are in
`../four-seven-template-link-independent/`.

The exact matching base matrix is
`7bfcfd3b82f52016c9c594778d19443b2ed803c1f6e121461230bda28cbfb0ee`.
It is also the matching matrix in the previously completed independent encoding
audit `../four-seven-template-hull/independent-audit.json`, whose SHA-256 is
`fe57e7e414426f9d9c5815d062aa82b56f363408582d8d88dc40967f1f2df7ef`. That audit checks the complete original-100
surviving template catalogs, all transports, all 4,270 original rows, and all
280 extension rows. Thus the three exact contradictions apply to their stated
regular four-sevenfold first-link branches, with that audited reduction chain.

`matching-077` was independently excluded by the separate six-case hub-count
campaign as well. The overlap is counted once: this screen leaves 153 of its
156 input representatives open and adds `matching-017` and `matching-083`
beyond that campaign's exclusions. The checked union is 105 excluded first-link
types out of the original 258, leaving 153 open. It does not establish an unrestricted
covering-number lower bound.

## Saved numerical evidence

`check_results.py` independently read all 156 result records and checked all
153 sparse primals. It uses integer arithmetic with a common power-of-two
denominator, so the reported residuals are exact calculations on the stored
binary floating values. It checks every base-plus-seven row, the unit bounds,
the lexicographically reconstructed fixed block IDs, source/matrix/log hashes,
recorded reset states, and remaining phase-one solver budgets. Six damaged
controls were rejected. Small nonzero residuals confirm only numerical
feasibility, not exact rational witnesses or covers.

Cycle primals have 376–422 fractional block values; matching survivors have
386–424. Neither case yielded a near-integral block selection for dual-verifier
candidate dispatch.

## Evidence identity

- Frozen runner: `c8841227df38eec07b28f9776e812e1df4c8c4175e80c0feead9fb15f8289b9e`.
- Full raw results: `b263485ab23815f579f046f36817e36110437504d8d8c30a60ab8c6af2186ebf`.
- Readback audit: `855f60ace92f5bc1adc9f02bb5a23cb0fbb907e67a5c7f1be2f21725cfe93681`.
- Independent readback checker: `2105a615be69d030442a0dbecc471f7e8354e75c86c53e901d181aca2488a2ed`.
- Console log: `772f8cbe6d17093bc5669288affe8bede517207449038a52ec107ad1f299c5c9`.
- Machine-readable summary: `c82c5ecacaf34a8566d862449c4f1540f459e6591d0973a7d3d07a3bb658f053`.

The raw run records retain their original pending-certificate flags. This
separate report records the later independent replays without changing the
frozen solver evidence. Large matrices, protobufs, primals, duals, certificates,
and copied sources remain under the ignored scratch run directory. The full
input hashes, source revision, OR-Tools version, command, and per-case solver
timings are in its `metadata.json` and individual result records.
