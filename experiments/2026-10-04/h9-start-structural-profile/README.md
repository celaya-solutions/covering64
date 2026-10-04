```text
Document:    H9 Start Structure and Radius Four Exclusion
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      9319e40eb675dd2a80b5cea39557005316102885613c82b997831668f4160c75
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Scope and evidence

This certificate concerns only the pinned 64-block family with hash
`f5f24d57738763380c715769eef4328d7f1950a8ae6d0eedd8e9ff16dc3fc681`.
It recounts its holes and multiplicities, checks all 4,368 possible added
blocks, and propagates unions of the resulting nine-bit masks. There are at
most 512 mask states. No solver, native search, four-adder tuple enumeration,
or new search kernel is used. Both real cover verifiers confirm the same nine
holes; four damaged input families are rejected. The saved profile binds the
source, initial witness, frozen queue manifest, completed native runtime audit,
and both verification receipts by SHA256.

# The holes and point links

The nine missing triples are:

```text
1 5 7       1 9 15      2 10 13
5 8 13      5 9 12      5 9 15
6 8 10      8 13 15     10 12 16
```

Triple multiplicities are 0:9, 1:464, 2:85, and 3:2. Thus no triple occurs more
than three times. Points 1 and 8 have degree 19, points 6 and 16 have degree
21, and every other point has degree 20. The weak measures remain D2max 23,
D2sum 29, minimum pair count five, and D3 = D4 = 0.

The link at point 1 consists of 19 four-blocks on the other 15 points. Its
pair multiplicities are 0:2, 1:92, 2:11; the two missing pairs are {5,7} and
{9,15}. All link point degrees are five except point 16, whose degree is six.
The link at point 8 has pair multiplicities 0:3, 1:90, 2:12, missing pairs
{5,13}, {6,10}, and {13,15}; point 12 has link degree six, all others five.
These are descriptions of this family, not incidence conditions imposed on
an unrestricted covering model.

# Exact hole-carrier bound

Among all five-blocks, 3,716 contain no original hole, 605 contain one, 44
contain two, and only three contain three. Those three blocks are:

```text
1 5 7 9 15
1 5 9 12 15
5 8 9 13 15
```

All three contain the hole {5,9,15}. Therefore three added blocks cannot cover
all nine holes: reaching nine with three blocks would require three disjoint
three-hole sets, which do not exist. The saved mask recurrence independently
gives maximum covered holes 3, 5, 7, and 9 for one, two, three, and four blocks.
The exact minimum for covering only these original holes is four. A witness is:

```text
1 5 7 9 15
1 5 8 13 15
2 6 8 10 13
5 9 10 12 16
```

These four blocks do not claim to repair any holes created by removing four
original blocks. Before considering those new holes, this already implies
that every exact 64-block cover has overlap at most 60 with the named initial
family. That necessary bound alone does not exclude radius four.

# Radius four is excluded by private triples

Suppose a full 64-block cover differs from this family in at most four blocks.
The hole bound forces exactly four additions and four removals. Any three
additions cover at most seven original holes. Consequently every one of the
four additions must cover at least two original holes; an addition covering
zero or one would leave the total below nine. There are exactly 47 allowed
additions under this necessary condition. None is in the initial family.

Call an original triple private when exactly one original block covers it.
For each of 63 original blocks, the certificate lists a private triple that
none of the 47 possible additions covers. Each of those 63 blocks must stay:
removing one would leave its private triple uncovered. Only the original
block {8,9,10,12,15} lacks such a witness. A four-block replacement would retain
only 60 originals, contradicting the 63 forced originals. This completes the
finite radius-four exclusion without enumerating any four-adder tuples.

It follows that **every exact 64-block cover has at most 59 blocks in common
with this named initial family**. This is a necessary overlap inequality,
not a global nonexistence result. The same statement transports when both the
initial family and the certificate are relabeled, but passing any fixed
named-image check does not establish escape from all images. No stronger
radius, no other queue family, and no new common62 core is certified here.

# Every image of each old 60-block core

The four pinned old cores each have five mutually disjoint triples, each
covered by six of their 60 blocks. A five-block cannot contain two disjoint
triples, so these five sets of six carrier blocks are disjoint. Every triple
in the H9 family occurs at most three times. Under any relabeling of any one
of the four cores, at least three of the six carriers of each heavy triple
must therefore be absent from the H9 family. This removes at least 15 distinct
core blocks and proves overlap at most **45 with every image of each old
core**. The source recounts each core and saves the heavy triples explicitly.
The argument does not apply to the new common62 core without a separate proof.

# Consequence for a later repair experiment

A radius-four exact residual model would be complete on the 64 original
blocks plus these 47 additions, with full triple coverage and exactly 60
originals plus four additions. The private-triple certificate already makes
that model infeasible, so running it would add no information. A structurally
new repair would require at least five exchanged blocks around this exact
start, or a different starting family whose corresponding bound is checked
again. Any future fixed residual neighborhood must keep all triple rows and
state its retained-block restriction; it must not impose this family's point
degrees or link structure on an unrestricted model.

Reproduction: run `uv run python` on `check.py` in an unfrozen copy of this
folder. The checker refuses to overwrite an existing profile.
