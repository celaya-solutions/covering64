~~~text
Document:    Complete Circulant Excess Profiles and Their Symmetry Classes
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      896a6fa7e70997e7ddffb1fbd8d056c0bdefb63dc1789584012bc71613920c79
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
~~~

Independent integer propagation and backtracking finds exactly the same 1,300
arithmetic excess profiles as the producer's rational elimination method. A
complete enumeration of the graph's 32 automorphisms partitions them into 52
classes. This classifies excess profiles for the fixed graph on Z16 with steps
{+1,-1,+3,-3,8}. It does not construct covers, prove cover existence, or give an
unrestricted lower bound for C(16,5,3).

## Reconstructed finite domain

The checker independently constructs every edge and enumerates all 6,435
unordered balanced cuts. Nine have cut size 32. A valid excess family has eighty
P3 triples, each nonedge in exactly one and each graph edge in exactly four.
For a tight balanced cut, the pair-excess sum across it is 64+3*32=160. Each
crossing triple contributes two, so all eighty excess triples must cross it.
Internal excess paths are therefore forbidden by the exact pair sums and
nonnegativity, even before asking whether a block cover exists.

Applying all nine tight-cut deductions leaves thirty-two forced nonedge-center
choices and forty-eight binary choices. The checker reconstructs every choice,
the forty edge equations, and their integer right-hand sides. A bit zero
selects the first listed center and a bit one selects the second. All saved
geometry and equations agree.

## Independent completeness method

The producer uses rational RREF with thirty pivots and eighteen free variables,
then checks all 262,144 assignments of those free bits. This independent
enumerator does not use the saved RREF, pivots, free columns, or producer code.
Instead, it converts each integer equation with coefficients -1,0,1 into an
exact cardinality row on positive or negative literals.

At each node, a row is rejected when its selected literals already exceed its
target or its selected plus unknown literals cannot reach the target. Equality
with the upper or lower attainable total forces every remaining literal in the
row. Once propagation stops, the first variable in a deterministically chosen
active row is assigned zero and one in separate recursive branches. These
branches are disjoint and exhaust every possible Boolean completion. No
symmetry assumption or numerical tolerance is used in this enumeration.

The completed traversal has 3,247 nodes, 1,623 binary branch points, 324 rejected
nodes, and 22,486 forced assignments. Its 1,300 distinct complete assignments
match the producer's entire sorted mask list exactly. Every assignment is then
expanded into eighty triples, and all 120 pair sums and sixteen point sums are
recounted independently.

As an additional check, the saved RREF is verified without using it for
enumeration. Its pivot columns form an identity matrix, and every original
augmented row is reconstructed exactly from its thirty nonzero rows. A separate
modulo-101 elimination gives a rank lower bound of thirty. Together these
checks establish rational rank thirty and affine dimension eighteen.

## Complete graph automorphisms and orbit certificate

Fix point one. Each of its ten nonneighbors has a distinct subset of neighbors
inside its five-point neighborhood. Thus the image of those five neighbors
uniquely determines any automorphism fixing point one. The checker tries all
120 neighborhood bijections, extends each using those unique signatures, and
checks every graph adjacency. Only identity and reflection survive.

Composing these two stabilizer maps with all sixteen cyclic translations gives
all 32 graph automorphisms. Completeness follows because any automorphism can
first be translated to fix point one. Every explicit map is saved and checked
to preserve all graph edges, forced paths, and binary center choices.

The exact action on the forty-eight bits is computed for each map. Every image
of every one of the 1,300 assignments stays in the solution set. The resulting
orbit partition is:

| Orbit size | Number of orbits | Profiles |
| ---: | ---: | ---: |
| 2 | 4 | 8 |
| 4 | 1 | 4 |
| 8 | 3 | 24 |
| 16 | 9 | 144 |
| 32 | 35 | 1,120 |
| Total | 52 | 1,300 |

Each orbit saves every member, its minimum mask representative and stabilizer
size. An independent Burnside count from all 32 fixed-point totals confirms
the same orbit count. The original eight translation-invariant profiles are
exactly the four size-two orbits; they pair as indices 0/7,1/6,2/5,3/4. There
are forty-eight further graph-symmetry classes. No cover is assumed invariant
under any of these maps.

## Complete point-link tally

All 1,300*16=20,800 point links have a five-edge core on the five graph neighbors
and ten pendant leaves. The complete core-type tally is:

| Core type | Point links |
| --- | ---: |
| C5 | 4,768 |
| C4 with leaf | 6,272 |
| Triangle with attached two-edge path | 8,512 |
| Triangle with leaves at distinct vertices | 1,248 |

The checker uses the exact degree sequence and triangle count to distinguish
these four types, verifies every noncore edge joins a leaf to the core, and
rejects any other signature. There are twenty-four profile-level distributions
of these types. Each saved global orbit includes its representative's type
counts, checked to be invariant across the orbit. This is a necessary local
shape statement; no particular block realization of a point link is fixed.

## Evidence and replay

Five changed-profile controls are rejected: omission, duplication, reversal of
the canonical list, a Boolean in place of a mask, and a changed bit that fails
an exact edge equation. The source uses only the Python standard library. It
performs no optimizer calls and no search over five-point block covers. Ruff
passes.

~~~sh
uv run python experiments/2026-10-04/circulant-all-excess-independent/check.py
~~~

The initial audit SHA256 is
0ac5ff70de498fd1f399eea6fc7988057d964a53ec0a614c276c0831bc1b3dd9.
The complete orbit certificate SHA256 is
d0aab8d3de76e07c23a71adb10d10b36e403275fd236f52522f38e0efac480d6.
The automorphism certificate SHA256 is
66bf50ad962eb0f1a260320e2a8ff9fad3531022174632cfa07fd5dbb9bb8512.
Replaying changes only the audit elapsed-time field and its file hash; the
enumeration, maps and orbit partition are deterministic.
