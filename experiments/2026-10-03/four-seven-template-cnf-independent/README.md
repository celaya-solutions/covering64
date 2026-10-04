```
Document:    Independent Restricted CNF Translation Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      cdffac94a17f63bbb2ef4e08c23e6c80f0738e99d39bafbffc72a195a78bf665
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# What was checked

Both CNFs encode the already audited restricted CP models for matching-029 with hub case (0,2), and matching-063 with hub case (0,1). Original variable i is DIMACS variable i+1. The audit binds the previous model audit and manifests, reconstructs all 9,118 rows, and streams every one of the 7,531,645 clauses. Clause and auxiliary boundaries, row normalization, source hashes and final dimensions must agree exactly.

Negative coefficient -a times x is represented as a copies of the literal not-x plus constant -a. Coefficient four repeats the identical literal four times. Repeated inputs therefore retain their weight and are not treated as independent new variables. Complementing all literals changes interval [L,U] to [n-U,n-L].

For threshold T(i,j), induction on i gives T(i,j) iff at least j of the first i literals are true. The base threshold T(i,0) is true and unreachable thresholds are false. The four checked clauses encode both directions of T(i,j) = T(i-1,j) OR (literal_i AND T(i-1,j-1)). Final unit clauses enforce the required lower and upper bounds. This argument remains valid for repeated and complemented inputs. The Sinz at-most-one chain is sound because any true input forces all later prefix markers true, excluding later true inputs; prefix-OR assignments extend every permitted input assignment. An added disjunction enforces exactly one where needed.

All seven encoding recipes were checked against direct integer predicates on 1,189 small rows and 4,756 assignments, including negative coefficients and repeated/complemented literals. The threshold gate passed all 16 truth assignments. Six malformed clause fixtures were rejected.

# Result and limit

The translation gate passed. This checks equivalence of two restricted encodings only. It does not itself solve either CNF or establish nonexistence. A solver UNSAT report must still have its certificate accepted by a separate proof checker before any exclusion is recorded. Large DIMACS files and any raw proof artifacts stay outside Git.
