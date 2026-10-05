```text
Document:    Prescribed-Group Orbit Covering Search
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      3e0ad0a04e70a3125275f948cb5b0aecf01b1c14c6bc58db23d3b2052dcfc9e2
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Prescribed-group orbit search

## Question

Is there a 64-block cover that is a union of orbits of some nontrivial
permutation group on the sixteen labels? Earlier work exhausted seventeen
regular order-16 actions (four-orbit selections) and left twelve cyclic CP
searches UNKNOWN. This campaign widens the family of groups.

## Model

For a group G, `km.py` partitions the 4,368 five-subsets and 560 triples into
G-orbits. A block orbit covers a whole triple orbit when one of its blocks
contains one triple of that orbit, so a G-invariant cover is a choice of block
orbits meeting every triple-orbit row. Block orbits whose covered rows are a
subset of another orbit's rows with no more blocks are dropped; swapping in the
dominating orbit keeps any cover a cover with no more blocks.

Implied rows are added for every cover: each point lies in at least 19 blocks
and each pair in at least 5, one row per point orbit or pair orbit. The total
must be at least 61 (Schoenheim) and at most the largest sum of orbit sizes not
exceeding 64. A group is screened out when no orbit-size sum reaches 61, or
when the numerical GLOP minimum of the relaxation exceeds that largest sum.
Otherwise CP-SAT decides feasibility within its time limit. Any feasible
answer is written out and must pass both cover checkers; none occurred.

## Groups

Candidates are every cycle type of S16 except the identity, plus each of
eighteen ambient groups and 150 random subgroup chains from each (product
replacement, one to three generators, often raised to powers to lower the
order): AGL(4,2), the Clebsch group 2^4:S5, AGammaL(1,16), AGammaL(2,4), a
Sylow 2-subgroup of S16, S4 wr S4, S4 wr S2 on a 4x4 grid, S8 wr S2, S2 wr S8,
S6 on 6+10 points, S6 on pairs plus a fixed point, S5 on 1+5+10, PGL(2,7) on
8+8, PGL(2,13) on 14+2, PGL(2,11) on 12+4, PGL(3,3) on 13+3, GL(4,2) on 15+1
and GL(3,2) on 7+7+2. Their orders were checked by closure. Groups are deduplicated by an orbit signature
(point orbits, triple and block orbit sizes, and block orbit coverage sizes);
non-conjugate groups with equal signatures may be skipped.

## Results

Run v1.1.0 (seed 2026100511, 20 seconds and one CP-SAT worker per group, eight
processes) produced 665 distinct groups; 4,917 duplicate signatures and 18
near-trivial groups with more than 1,500 block orbits were skipped.

| Outcome | Groups |
|---|---:|
| Orbit sizes cannot total 61 to 64 | 121 |
| Numerical LP minimum above the reachable total | 451 |
| CP-SAT INFEASIBLE | 6 |
| UNKNOWN at 20 seconds | 87 |
| Cover with at most 64 blocks | 0 |

Every group of order at least 21 was settled. The 87 unsettled groups have
orders 3 to 20, mostly 4, 6 and 8 with point orbits such as 8+8, 8+4+4 and
4+4+4+4. A second pass (v1.2.0, seed 2026100521) gave each of those 87 groups 120 seconds and two CP-SAT workers. One more group, an order-20 subgroup of the Clebsch group with point orbits 10+5+1, is INFEASIBLE; the other 86 stay UNKNOWN. In total 579 of 665 groups are settled and none admits an invariant cover with at most 64 blocks.

## Evidence and scope

The executed v1.1.0 source is archived verbatim as
`executed-source-v1.1.0.txt` (SHA256
`224bdae402210441c20eb91479a06b096ea5d32a8e3b4543d8a5b4ffc2324d58`); `km.py`
v1.2.0 only adds the rerun option. `results-v1.1.0.jsonl.gz` and the rerun
results list every group with generators, order, orbit counts and outcome.
An earlier v1.0.0 pass without implied rows was stopped after 117 groups and
superseded; its raw output stays in ignored scratch.

As a positive control, the Z16 model with an 80-block cap returned an 80-block
cover that both checkers accept (canonical SHA256
`ea122b31c2119c90cb94067436c99d8296b5e47a28f3a9008407e96a89413f48`).

LP screens are floating-point and CP-SAT INFEASIBLE is not independently
checked. Every result applies only to covers invariant under that generator
set. No global claim follows.
