```
Document:    H6 Two Point Star Repair Independent Gate Review
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      97b5451e379aadcd5daac5a2ea2e6ab159c599e7c415011a4f93cf66e73592e5
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent gate for the H6 two-point star pilot

Decision: GO for exactly one root-launched call. This review launched no optimizer
or native process. It reconstructed the frozen model without invoking the producer
builder or solving any model, then tested the runner with mocked processes.

All 4,928 variable domains, 1,242 rows, the exact objective, and the complete hint
match the stated neighborhood. Among the 4,368 lexicographic block variables,
2,002 blocks avoid {6,10}; their original memberships are fixed, with 30 selected.
The other 2,366 memberships remain free. Exact cardinality 64 therefore requires
34 selected free blocks. There are 560 binary hole flags, each equivalent to its
triple having no selected covering block; every triple has all 78 possible block
carriers included. Each of the 120 pair rows has all 364 carriers and floor five.
The hole count is at most six, and the objective minimizes that exact count.

There are no additional assumptions, search strategies, core caps, degree rules,
D2/D3/D4 rules, or rotational restrictions. Every row and variable was compared
against an independent expected proto, including coefficients, domains, and
both directions of each hole equivalence. Sixteen damaged models were rejected.

The complete initial hint is deliberately infeasible. It violates exactly rows
1164, 1175, and 1221: pairs {4,6}, {5,6}, and {10,12} each have count four.
The remaining domains and active rows pass. The hint is not fixed by solver
parameters and is never claimed to be a feasible candidate.

The frozen call uses 120 seconds, four workers, and seed 2026106001. The parent
watchdog allows 140 seconds, followed by a five-second termination grace before
kill. Independent mocks checked normal exit, termination, and kill; each path
launched exactly one mock process and rejected a repeated execution. Source review
also checked the child preflight, exclusive start marker, single solve call,
complete-vector callback, early stop on zero holes, and dual saved-family checks.
The producer's 23 mock-only preparation controls are bound and reviewed.

Root alone may execute the approved call. There is no restart, extension, or
unused-budget transfer. This is a fixed neighborhood only. UNKNOWN and timeouts
are inconclusive. A CP-SAT INFEASIBLE result would remain an uncertified local
solver result and would not establish unrestricted infeasibility.

The frozen gate is `gate.json`; full bindings and independent evidence are in
`checks.json`. `check.py` reproduces the review in a checkout with existing audit
receipts preserved elsewhere. It refuses to overwrite its receipt. Ruff passes.
