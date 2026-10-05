~~~text
Document:    Complete Independent Replay of Chosen Link Support Results
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      7f0b45c3787382669233dde1e55b8610fc6fa44e9da3fd3936d251d713c33a6a
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
~~~

Every one of the 195,296 saved cases passes independent verification. The screen
excludes 185,068 chosen-link/profile pairs and leaves 10,228 pairs with no
contradiction in this single support pass. These survivors are not asserted
feasible. The result concerns only all isomorphism images of the four chosen
saved point-link constructions, not every possible point link or every cover
with the named circulant pair profile.

| Checked outcome | Cases |
| --- | ---: |
| Insufficient residual support | 156,846 |
| Contradiction among immediately forced blocks | 28,222 |
| Survives the single pass | 10,228 |

## Runtime and file integrity

The producer completed its exact prefix [0,195296), with no missing or repeated
case ordinal. The external wrapper recorded 20.226166457985528 seconds for the
whole child process, including final hashing and output. The child reported
20.182739250012673 seconds for its processing phase. It exited zero with no
watchdog, termination, kill or stderr output.

The audit rehashes the original manifest dependencies, full producer source,
approved gate, independent catalog audit, watchdog source, runtime receipt,
captured streams, terminal producer result, proof stream and survivor stream.
Captured stdout parses to exactly the terminal result. All hashes agree.
The forty-five-second budget remains a cooperative processing budget; the
external wrapper supplies the separately recorded fifty-second watchdog and
five-second termination grace. Both observed durations were below their limits.

## Independent certificate checking

The checker imports neither producer and does not rerun the screen. It builds
the complete residual carrier matrix in the opposite direction: for each of
the 455 triples, it enumerates every pair of extra points among the other
twelve labels. This yields all sixty-six legal residual carriers. It verifies
that each of the 3,003 point-one-avoiding pentads occurs in exactly ten rows.
The full deterministic partial/profile pair order is separately reconstructed.

For each record, the checker rebuilds the residual demand and eligible domain
from the actual fixed blocks and excess triples. Its eligible-domain count and
hash must match the saved record. Each insufficient-support certificate must
list the complete support of its cited row, and that support must be strictly
smaller than the exact demand.

For a forced-conflict certificate, every listed forced block must belong to
the contradicted row. Every forcing cause is separately checked: its saved
support must equal the complete eligible support, support size must equal the
row's exact demand, and the forced block must belong to that support. The
certified forced blocks must exceed the target triple or cardinality demand.
This validates the mathematical contradiction directly, without requiring the
producer's choice of first failed row or first forcing cause to be trusted.

For every survivor, all 455 row supports are checked. The complete set of
immediately forced blocks is reconstructed, and every triple upper bound and
the remaining cardinality forty-four are checked against that set. Its count
must match the record. The separately saved survivor stream must match exactly
all 10,228 independently checked survivor identities in order.

The saved operation counters also sum to the producer's receipt. Their exact
per-case first-row behavior was independently replayed for all 1,000 benchmark
cases in the earlier gate; the complete runtime checker instead verifies every
actual exclusion certificate and every survivor's full arithmetic.

## Controls, timing, and scope

Six damaged records are rejected: wrong failed-row demand, missing support,
wrong eligible-domain hash, wrong forcing demand, missing forcing support, and
wrong survivor forced count. The final complete replay took 5.400178291019984
seconds under a separate 120-second cooperative verification budget. Its prefix
and complete_replay fields would limit the claim if that budget were reached;
the full record set was verified here. Ruff passes.

There were zero optimizer calls, zero producer reruns, and no iterative
propagation or new cover search. The 185,068 exclusions are finite certificates
for their chosen cases. The remaining 10,228 cases require further work before
any feasibility or impossibility claim.

~~~sh
uv run python experiments/2026-10-04/circulant-chosen-link-support-runtime-independent/check.py
~~~

Final audit SHA256:
d2e5259ab156ff81111742f4c1d8068a436685278bac5fdc9f7a82af34df6137.
Checker SHA256:
34454b7922b3165000622ab7a810d316f2a511e1f0181e23a450b35209afbc95.
Producer result SHA256:
aabd7d06c2a2b297b69086676e12a68ccfd6a532dcf5ea3aeca53d42fde958e3.
Replay timings and therefore the audit hash change on a later replay; the
source, input pins, complete checked case set and outcomes remain deterministic.
