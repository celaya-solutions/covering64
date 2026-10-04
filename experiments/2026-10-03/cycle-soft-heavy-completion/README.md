```text
Document:    Cycle Soft-Best Heavy-Template Completion
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      2cf5896a78dfc6096bc441f89e7a7ce4804b0d7b4b3e69e74d78524d0c377ed9
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Completion result and a small direct obstruction

The root independent gate passed in the sibling directory
`cycle-soft-heavy-completion-independent/{check.py,audit.json}`. It compared
all original protobuf fields and the exactly 28 appended heavy-block
identities. The approved CP-SAT pilot used one worker, seed 2026104101 and a
60-second limit. It returned INFEASIBLE during presolve after 0.014561 native
seconds (0.349189 measured wrapper seconds), with no witness. That solver
status alone is not an independently checked theorem.

A separate exact-count certificate now explains the obstruction without a
solver. The heavy tuple does not cover triple (3,11,15). Exactly 18 legal
ordinary blocks could cover it. Each candidate, together with just seven of
the selected heavy blocks, exceeds a pair's available excess. All blocking
pairs touch an anchor point and have forced pair count five. The standalone
checker recounts every case, checks the entire 18-block candidate inventory,
validates the four complete heavy templates, and rejects eight damaged
controls. The certificate does not assume the soft targets on hub-only pairs.

`heavy-obstruction.json` contains the seven supporting heavy blocks and the
18 explicit candidate/blocking-pair records. `check_obstruction.py` uses only
the Python standard library. Its receipt is `heavy-obstruction-audit.json`.
This excludes only this fixed heavy tuple inside the degree-20 native family.
It does not change any first-link exclusion registry or global bound.

# Why the pair budgets are necessary for a zero-hole native state

Every pair must occur at least five times: its 14 triples need coverage,
and each containing 5-block covers only three of those triples. For an
anchor point a, its two anchor peers occur with a at least seven times due
to the seven fixed heavy blocks. Its own hub h occurs in two of those heavy
blocks. Thus the two triples consisting of a, h and one other anchor point
are both already doubled. The pair (a,h) consequently needs at least 16
triple occurrences, so its block count is at least six.

Point degree 20 gives total pair incidence 4*20=80. The lower bounds just
proved already sum to 7+7+6+12*5=80. Therefore every pair touching an anchor
point has its exact necessary count: seven with an anchor peer, six with its
own hub, and five with every other point. No hub-only pair target is needed.

For a pair p of exact count L, any full cover has exactly 3L-14 excess triple
occurrences on p. For a partial set S, let
E_S(p)=sum over triples t containing p of max(0,count_S(t)-1).
Completion can only increase this quantity, so E_S(p)<=3L-14 is necessary.
All 18 certificate blockers have L=5, budget one and partial excess at least
two. The seven supporting blocks are a small sufficient subset; no claim
of minimum support size among all possible proofs is made.

# Constructive rule

For a complete four-template tuple H, compute all heavy triple counts and
these excess budgets on anchor-touching pairs. A proposed ordinary block B
adds one to the excess for each of its triples already covered by H. Reject
that ordinary candidate if any necessary pair budget would be exceeded.
Then count H-uncovered triples supported by no surviving ordinary candidate.
Such a tuple cannot yield a zero-hole degree-20 native state. Cache this
count per heavy-template tuple; ordinary-only moves do not change it.
A high soft penalty can guide whole-template choices while keeping the native
search's unconditional zero-hole save behavior. Hub-only targets stay soft.

# Saved diagnostic model

The model copied the audited cycle base with 4,768 Boolean variables and
4,270 constraints, adding exactly 28 selected-heavy-block equalities. No
ordinary block, hint, objective or hub-count case was added. All original
protobuf fields remain unchanged. The seed has 12 holes and score 92, with
catalog template IDs 20588,13504,5835,20047. The 4,298-row model SHA256 is
`ac8931997f965440408e1c975deba00a747e049f2f45b6d38e3ee2f675e5fbb9`.
Version 1.0.1 only wrapped a report string for Ruff; its preserved version
1.0.0 preview has identical model bytes. The raw pilot keeps logs, parameters,
response, source snapshots and hashes. No further solve was used to find or
check the small excess-budget certificate.
