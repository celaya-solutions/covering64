```
Document:    Existing Hint Pair-Link and Heavy-Hub Diagnostics
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      63461a7e5e48c855ba1b301fd1a6d42cb232eed1a135e461a9ad16340124d97e
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Existing hint pair-link and heavy-hub diagnostics

None of the 17 distinct states eligible under the bounded pair-floor inventory
passes both proposed pair-link cut families. This is a read-only recount of saved
states. It changes no model, hint, parameters, or optimization result. The exact
agent is auditing the unrestricted validity of the cuts separately.

For every pair P contained in a triple T, the diagnostic checks
`3*c(P) - c(T) >= 13`. For every pair P contained in a quadruple Q, it checks
`3*c(P) - 2*c(Q) >= 12`. Each state receives all 1,680 triple-row and 10,920
quadruple-row checks: 28,560 and 185,640 checks across the 17 states.

## Selected six-hole hint

The prepared pair-floor model retains the selected six-hole hint, SHA256
`797dada195b23eecc808798eb12c8e4e7ccd7edd026fbdf22dea5b341f9ea2de`.
It violates four triple rows, each by one, and no quadruple rows:

| Pair P | Triple T | c(P) | c(T) | Left side | Required |
| --- | --- | --- | --- | --- | --- |
| {4,7} | {4,7,12} | 6 | 6 | 12 | 13 |
| {4,12} | {4,7,12} | 6 | 6 | 12 | 13 |
| {10,14} | {10,14,15} | 6 | 6 | 12 | 13 |
| {10,15} | {10,14,15} | 6 | 6 | 12 | 13 |

All sixteen points have degree 20. Its heavy-link endpoint counts are:

| Heavy triple | Multiplicity | Repeated outside hub |
| --- | --- | --- |
| {1,2,3} | 7 | Point 4, degree 2 |
| {4,7,12} | 6 | None |
| {5,8,11} | 7 | Point 10, degree 2 |
| {10,14,15} | 6 | None |

The two hubs are distinct, so this specific seed does not reuse a hub. Each hub
lies inside another heavy triple. These structural facts explain which stronger
necessary conditions the seed fails; they do not invalidate its use as a
near-cover hint in the currently frozen model.

## Other eligible saved states

The alternate six-hole state has three violated triple rows with total deficit
five and one violated quadruple row with deficit one. The documented native
v1.3 twenty-hole scored-qualified state, SHA256
`3057f9f3e72e787d58bd585a0e3fe091af84f2bc2982088fc0a785012d0ffbb7`,
has two violated triple rows with total deficit two and no violated quadruple
rows. Thus the older label “passes all scored necessities” does not include
these new diagnostic families.

No fully legal hint for a model imposing both stronger families was found in
this declared inventory. Any next model or native continuation should use this
fact explicitly; a zero diagnostic penalty would still not establish a cover.
The current 120-row pair-floor model, its six-hole hint, and its recorded run
remain unchanged.

`pair-link-diagnostics.json` preserves every violated row, exact counts, degrees,
heavy triples, endpoint degree lists, reused-hub counts, and hub containment
relationships for all 17 states. Its SHA256 is
`faebd03a3a1e1dfb3509b37486f8625bc3ee8814d73abf7c1eabe4df06c236a5`.
`diagnostic-files.json` binds that result, its source, this report, and the frozen
input inventory. No optimizer was invoked by this diagnostic.
