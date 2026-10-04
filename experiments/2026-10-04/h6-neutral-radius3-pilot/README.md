# Neutral H6 neighborhood pilot

~~~text
Document:    H6 Neutral Radius-Three Coverage Enumeration Pilot
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      a3fb3f7522edc90b49daabc9b77ea041d35c33ab4e08fb648e6f53cc9446ad28
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
~~~

## Prepared search

This deterministic pilot is prepared for a sole root launch after independent
review and a matching gate. Preparation runs only tiny v7 fixture controls,
malformed-input controls, a zero-budget H6 parsing control, and short Python
process watchdog controls. It does not explore a real-H6 replacement tuple.

The input is the raw exact64 H6 family with SHA256
2d018ffa5e3e424193a4197b23891b52fa59b7ca411d06108e0ab1666bb85855.
It fails pair floor five and remains a valid input. The pilot enumerates exact
replacement distances one, two, and three, retaining every distinct family with
at most six holes. All 4,304 pentads outside the entire original family are
eligible additions. Labels are 1-based and block IDs are lexicographic.

The native time cap is 30 seconds. The wrapper watchdog is 35 seconds, followed
by termination and a five-second grace before a forced kill if necessary.
There is one process and one production launch, with no restart or transferred
budget. Natural exhaustion and timeout are distinct outcomes. Completing all
three shells requires 64, 2,016, and 41,664 deletion sets respectively.

## Coverage-only pruning and evidence

After deleting k blocks, let U be the uncovered triple set and q = |U| - 6.
The sum of the k largest eligible adder coverage counts bounds every union
from above. A sum below q safely excludes the deletion set. Each participating
adder must have count at least max(0, q minus the k-1 largest counts). This
necessary floor remains safe if the bounding counts include the adder itself.
When q is zero, every adder remains eligible.

Every unordered distinct k-tuple in the resulting pool is checked by exact
residual-mask union. The residual universe has at most 36 triples and fits in
a checked 64-bit mask. Different full blocks remain distinct even when their
masks match. Deletion count updates are restored before the next deletion set.
No pair, weak, degree, or core condition filters the search.

The checked preliminary deletion screen gives a necessary workload of three,
1,043, and 185,917 addition tuples for the three shells, totaling 186,963.
The pilot recomputes all deletion sets, rather than trusting a survivor list.
The screen is a workload estimate, not proof of a weak-qualified endpoint.

Every saved candidate is retained, checked for its exact distance, and passed
through both the package verifier and the separate standalone checker. Both
verifier receipts are saved in the result. Only afterward does the runner
classify minimum pair count, D2max, D2sum, D3, D4, and the six named core overlaps.
Pure endpoint weak qualification means pair floor at least five and D3 = D4 = 0.
The result reports it separately from weak qualification with all six caps.
A complete cover is recognized from the two verifiers regardless of these
endpoint classifications.

## Controls and limits

Three v7 fixtures are checked against exhaustive unpruned deletion/addition
enumeration, including a redundant starting block that gives zero demand.
All candidate identities and hole counts must match. Control receipts pin
fixture inputs, ledgers, and aggregate witness inventories. Invalid witnesses
and invalid budgets are rejected. Process-control fixtures check normal exit,
watchdog termination, and forced kill of a child that ignores termination.

The launch gate must bind the exact manifest hash and explicitly permit launch.
Every manifest dependency is rehashed first. Full candidate families, native
logs, timeout state, and shell counts are preserved. A killed process may leave
an unledgered raw partial file; this is counted and retained without treating
the interrupted search as complete.

Completion only concerns the at-most-six-hole neighborhood of this named input.
The separate strict-radius-four result already found no strict improvement
there, but it is not used as a search filter. Neither neighborhood result is
an unrestricted lower bound. The goal remains a verified cover.
