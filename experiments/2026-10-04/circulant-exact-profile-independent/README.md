```text
Document:    Independent Eight Circulant Exact Profile Model Gate
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      e9309db0b5995750e39c0b53800fdf0f2e2457a8f16f7fedd60f778798ad4cb2
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent circulant model gate

Decision: GO for the frozen eight-call manifest, with the hashes in gate.json. All 27
producer pins agree, including the separately checked arithmetic profiles, source,
verifiers, and sixteen model/parameter files. The audit makes no solver call and sends
no real process signal. Root alone owns production launch.

Every one of the eight serialized models has exactly 4,368 free Boolean variables in
lexicographic block order, one exact 64 cardinality equation, and all 560 exact triple
equations. Each triple has all 78 block carriers with coefficient one. Its demand is one
for 480 triples and two for the 80 saved excess triples. No variable domain is fixed;
there are no extra rows, local links, neighborhoods, guards, hints, objectives,
assumptions, custom search strategies, or serialized symmetry constraints. In particular,
no Clebsch or previously chosen affine-link restriction enters these models.

The independently checked arithmetic uses a different triangle-free five-regular graph,
Z16 with steps {+1,-1,+3,-3,8}. The excess profile is fixed in each model. The block family
is not constrained to be invariant under translation. Reflection x→−x maps profile
indices 0↔7,1↔6,2↔5,3↔4; this exact pairing is independently checked. The frozen eight
calls therefore include equivalent profile pairs, and no claim of eight nonisomorphic
profiles is made. The audit does not silently change the authorized eight-call budget.

The eight seeds are 2026106401 through 2026106408. Parameters contain only the exact
seed, 30-second limit, one worker, progress logging, and log_to_stdout=false. Maximum
native budget is 240 seconds. The wrapper uses a 35-second watchdog and five-second
termination grace. It runs sequentially, with no retry or budget transfer, and stops
on a watchdog, nonzero exit, missing child receipt, or MODEL_INVALID.

Twelve malformed model controls are rejected: a fixed variable, nonbinary domain,
repeated carrier, wrong coefficient, weakened demand, wrong cardinality, guarded row,
extra link restriction, objective, hint, assumption, and search strategy. Nine mocked
launcher scenarios pass: normal eight calls, terminate, kill, nonzero exit, missing
child, invalid model, invalid gate, mismatched manifest gate, and existing child output.
The normal scenario also rejects another launch. All Popen and solver operations are
mocked during those controls. Ruff passes.

A feasible result must be an exact 64 cover matching the exact profile and pass both
package and standalone cover verifiers. UNKNOWN is inconclusive. INFEASIBLE without a
separately checked proof certificate is not a theorem. Results remain conditional on
these eight excess profiles; other excess profiles for the same graph and unrestricted
C(16,5,3) remain outside the models.

The checker refuses to replace its saved review and checks that production has not
started. A changed manifest, source, profile, model, or parameter file needs a fresh
audit and gate. The saved seed-check receipt is hash-bound; this review does not recreate
its historical filesystem search.
