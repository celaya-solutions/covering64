```text
Document:    Independent CP-SAT Cross-Check of the 61-Block Case
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-06
SHA256:      d9b1ffaa64401c701784530c8d15a5294f2de758067134c0661b972e4f351427
Chain:       solana-mainnet
Tx:          2a6mLGXGZ4Nkvs32TTM9rT4Q4aXxSaTkZr4vwPAMvzJFZQ45za5tfG1dj2MTcbWsSrUHy4HzNXZREABqqgVZvsW
License:     CC BY 4.0 / Celaya Solutions
```

# Independent cross-check

`cpsat_check.py` states the same four fixed-link problems directly as linear
constraints in CP-SAT, written separately from the CNF encoder: exact link
blocks at point 1, every triple covered once or twice, every pair covered
5 + [pair in E] times, and one or four doubled triples per pair. The runs
started on 2026-10-05 at 10:42 MDT (OR-Tools 9.15, 3 workers, 3,600-second
limit each); the saved script differs only by its filled header line.

| Link class | CP-SAT status | Time |
|---|---|---:|
| shape-1 | INFEASIBLE | 1,623 s |
| shape-4 | INFEASIBLE | 1,926 s |
| shape-44 | INFEASIBLE | 2,089 s |
| shape-47 | INFEASIBLE | 1,918 s |

All four agree with the CNF refutations. CP-SAT INFEASIBLE is supporting
evidence; the certificates are the DRAT proofs in `../lb61-certified/`.
