```text
Document:    Independent Seven Affine Link Completion Model Gate
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      94efeaf360dd6a6e24b2b29c740910df9fb7d9e246009cd4eb7e160b8800ebc3
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent model and launcher gate

Decision: GO for the seven prepared conditional completion calls, with the exact manifest
and runner hashes in gate.json. Only the root agent owns production launch. The audit
made no optimizer call, real subprocess launch, or real signal. This gate does not claim
that any model has a feasible solution.

Every saved model was parsed and checked against independently enumerated lexicographic
C(16,5) blocks and C(16,3) triples. All seven models contain exactly 4,368 Boolean block
variables, 560 exact recipe-demand equations, one exact64 cardinality equation, and
1,365 singleton point-membership equations. The singleton rows select the exact twenty
saved link blocks and reject every other block containing that point. All 3,003 blocks
avoiding the point remain Boolean and unfixed. There are no additional rows, guards,
objectives, hints, assumptions, symmetry data, or search strategies. The finite support
screen is not used to prune the serialized model.

The seven profiles, partial files, dual-verifier receipts, and all 455 residual demands
per case agree with the independently checked constructions. Each partial has twenty
blocks, 185 covered triples, and 375 holes, and leaves total residual demand 440 for
44 additional blocks. The cases are exactly the independently checked screen survivors:
(0,10), (40,13), (4,7), (18,3), (16,3), (16,8), and (60,3), where each pair is
(profile seed, fixed point).

The solver parameters contain exactly random_seed, max_time_in_seconds,
log_search_progress, num_search_workers, and log_to_stdout. The seven distinct seeds
are 2026106301 through 2026106307. Each case has 30 solver seconds and one worker,
with a 35-second process watchdog and five-second termination grace. The maximum
solver budget is 210 seconds, with seven sequential calls and no retry or budget transfer.
The producer's prior unused-seed search receipt is pinned; this audit verifies its
saved binding, not historical filesystem contents.

Twelve damaged model controls are rejected: nonbinary domain, repeated incidence,
wrong coefficient, weakened demand, wrong cardinality, changed fixed membership,
guarded row, added restriction, objective, hint, assumption, and search strategy.
Five mocked launcher controls pass: normal completion, SIGTERM after watchdog,
SIGKILL after grace, exactly seven ordered calls, and rejection of another launch
through the exclusive start marker. All process and signal operations were mocked.
The runner's pin check was also exercised read-only. Ruff passes.

The runner checks every frozen dependency before each child, and each child reparses
its frozen model and parameters. A feasible status must provide an exact64 witness,
match every recipe triple demand and fixed point membership, and pass both cover
verifiers. UNKNOWN is inconclusive. CP-SAT INFEASIBLE without a separately checked
proof certificate is not an independent theorem. Any result is conditional on one
chosen link and its fixed recipe, not a claim about all local links or general existence.

The checker refuses to replace its receipt and checks that production has not started.
Use the frozen review and gate for this launch; any changed model, parameter, input,
or runner requires a fresh audit and gate.
