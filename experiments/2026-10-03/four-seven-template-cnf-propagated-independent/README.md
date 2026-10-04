```
Document:    Independent Forced-Value and Reduced CNF Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      7b5bca0f1476ea5caffee9c1edfa6b3f824404e6dceaacbc6feb53f70b9722ad
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Scope

This gate covers only the propagated matching-063 model. It is linked by hash to the already audited restricted CP model and threshold-circuit checker. It does not establish infeasibility or a new covering witness.

# Forced values

Each original signed linear row is rebuilt with duplicate coefficients combined. Exactly-one rows are translated algebraically with the correct complement constant. For each recorded deduction, previously proved Boolean values determine the constant part; the signs of the remaining coefficients give exact independent-variable minimum and maximum bounds. A variable is forced only when one of its two possible values has a row interval disjoint from the required bounds. Each batch is checked against the same previously established values, then applied simultaneously. Source-row identities, support dependencies, every bound and the final assignment/reason inventory are replayed.

All 2,928 recorded steps and 15,663 proved values passed. The checker reconstructs every explicit unit and every substituted original row, including clipping to achievable bounds, and requires the entire residual protobuf to match. It then streams and checks all 2,285,639 DIMACS clauses and every auxiliary/trace boundary. Eight damaged arithmetic, dependency and assignment controls were rejected.

The substitution is equivalent because all retained explicit units were proved from the original conjunction, and each original equation is preserved after substituting those units. Large raw CNFs and any proof artifacts remain outside Git. A separate proof checker must still accept a completed solver certificate before any new exclusion is recorded.
