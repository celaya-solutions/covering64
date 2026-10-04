```text
Document:    All Excess Profiles for the Named Circulant Pair Graph
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      214ffe6b736da267e76b21df9ddce34e923b7224a196aaaee3a49f1c2238fadb
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Complete finite arithmetic enumeration

The producer finds exactly 1,300 excess profiles for the graph on Z16 with
steps {+1,-1,+3,-3,8}, after all nine tight balanced-cut deductions. This is
an enumeration of repeated-triple choices for one pair graph, not a cover
construction or an unrestricted reduction. Independent replay confirms the list.

Under the named pair profile, pairs on graph edges have multiplicity six
and other pairs have multiplicity five. The checked triangle-free excess
argument forces every excess triple to be a two-edge path. Each nonedge
chooses exactly one common center, and every graph edge lies in four chosen
paths. A tight balanced cut forbids an excess triple wholly inside either
side. Rebuilding all nine cuts leaves 32 forced centers and 48 binary choices.
No invariance assumption is placed on those 48 choices.

For each graph edge, subtract the contribution obtained by choosing the first
available center for every nonedge. Switching a binary choice changes its row
by -1, 0 or 1. The resulting 40 integer equations in 48 binary variables have
rank 30 over the rationals. Exact Fraction elimination supplies their saved
reduced row echelon form and 18 free columns. The remaining ten rows are zero,
including their right-hand sides.

Every binary solution gives a distinct binary assignment to these free
columns. Conversely, each free assignment determines all 30 pivot values
uniquely. Enumerating all 262,144 free assignments and retaining precisely
those with binary pivot values is therefore complete. Integer subset-sum
tables evaluate the pivot equations without floating point. All 1,300 retained
assignments are separately recounted against the original 40 equations and
all 120 pair demands. Every retained profile has 80 distinct excess triples.

`geometry.json` retains the graph, cuts, forced choices, binary alternatives,
original matrix, right-hand side, pivot order and exact rational reduced rows.
All point labels in saved geometry are one-based; column indices are
zero-based. `profiles.json` stores sorted 48-bit choice masks, using the saved
choice order and center index zero or one. These are profiles, not 64-block
witnesses. No optimizer or cover search is called.

The complete calculation took 0.29003058304078877 seconds under a 60-second
finite budget. An incomplete run raises an error without writing a completion
receipt. The saved script SHA256 is
`73a8f632af2318c1cba856bbda5de211331484929144f19fc0c4ec0530e661fa`;
the profiles SHA256 is
`9e29e1aa6769950297656c4b4a14bef14f04bd182500dfc15e56ffb38b9fef9e`.

## Independent replay and relabeling classes

A separate integer row-bound and binary-branch engine, without RREF, finds
the same 1,300 masks in 3,247 nodes, with 1,623 branches, 324 pruned nodes and
22,486 forces. Exact row reconstruction and rank modulo 101 also independently
verify rational rank 30. Five damaged profile or geometry controls are rejected.

The graph has exactly 32 automorphisms. A map fixing point one is determined
by its permutation of the five neighbors: the other ten points have distinct
neighbor subsets inside that set. Exhausting all 120 neighbor permutations
leaves only identity and reflection. Composing these with sixteen translations
gives the complete group. Its explicitly checked action on all 1,300 profiles
gives 52 orbits: four of size two, one of size four, three of size eight, nine
of size sixteen and thirty-five of size thirty-two. The original eight
translation-invariant profiles occupy the four size-two orbits. These are
orbits of excess profiles, not orbits of covers.

All 20,800 point links retain the four earlier core classes: 6,272 C4-with-leaf,
8,512 triangle-with-path, 4,768 C5 and 1,248 triangle-with-distinct-leaves.
There are 24 profile-level type-census patterns. The independent audit SHA256 is
`0ac5ff70de498fd1f399eea6fc7988057d964a53ec0a614c276c0831bc1b3dd9`;
the orbit data SHA256 is
`d0aab8d3de76e07c23a71adb10d10b36e403275fd236f52522f38e0efac480d6`.
