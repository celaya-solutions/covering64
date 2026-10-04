```text
Document:    Complete Degree-Nineteen Search Roadmap
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      d6cda702fc44be6eca138edc67fbee2623c27aa078195ce326503a0d36dabc0e
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Complete split within the degree-19 branch

Every point of a cover with at most 64 blocks has degree at least 19. The
previously audited split leaves either a degree-19 point or the all-degree-20
regular case. In the degree-19 branch, fix one such point as 1 and use one
of the four independently classified point links.

If point 1 is the only degree-19 point, the degree sum is at least
`19 + 15*20 = 319`. It is a multiple of five and at most 320, so it equals
320 and there are exactly 64 blocks. Precisely one other point has degree
21; the other fourteen have degree 20. The verified full-link automorphisms
reduce the possible degree-21 points to 38 orbits across the four first-link
classes: 8, 11, 10, and 9. Every one of these cases retains all completions
with that exact degree profile; the degree-21 point need not be the link hub.

If at least two points have degree 19, select an ordered pair. The first
point's verified link has neighbor multiplicities five or six, so their
shared block count is exactly five or six. A smaller cover in either case
can be extended to 64 distinct blocks while preserving both selected degrees
by adding unused blocks avoiding both anchors. There are `C(14,5)=2002`
such blocks, far more than the number already selected or needed. Thus an
exactly-64 search is existence-preserving in both overlap cases.

This gives three degree-19 subcases: a sole degree-19 point; two such points
sharing five blocks; and two such points sharing six blocks. They may overlap
under different choices of anchors when several degree-19 points exist;
disjointness is not required for completeness. No second degree-19 point is
assumed in the sole-point subcase. This roadmap does not settle any subcase.

# New work and previously completed work

The six-overlap enumeration already has 270 ordered representatives and 196
classes after anchor reversal, with six independently certified local
exclusions. The original four single-link 300-second pilots were inconclusive.
Repeating those pilots is not the proposed next step.

The five-overlap case is explicitly outside the existing six-overlap audit.
Its second anchor can be chosen from 34 non-hub point orbits across the four
first links: 7, 10, 9, and 8. Enumerate compatible second links through their
five prescribed shared blocks, independently audit completeness, and then
screen the resulting 33-block unions with exact residual certificates for
31 additions. Every conditional completion retains all 2,002 possible blocks
avoiding both selected anchors.

The elementary residual-pair bound does not improve the existing single-link
model. A pair appearing `m=1` or `m=2` times in the fixed link has
`13-2*m` uncovered outside third points, so the rounded requirement is
`ceil((13-2*m)/3)=5-m`, exactly its existing pair bound. The graph blossom
formula also cannot be copied onto a pair link, whose residual blocks are
three-element edges. Any new local hull or parity cut needs a separate proof.

# Orbit evidence

`check.py` rechecks every supplied permutation against every block of the
corresponding full first link, checks group closure, and recomputes all point
orbits. `orbits.json` records source and witness hashes and every case ID.
The supplied groups are previously audited full automorphism groups; even a
valid subgroup would give a safe, possibly finer, partition. The four-class
link completeness claim remains supported by its separate classification
replays, not by this short orbit check.

| Case ID | Degree-21 point orbit |
| --- | --- |
| `single19-shape1-high21-2` | 2 |
| `single19-shape1-high21-3` | 3, 4 |
| `single19-shape1-high21-5` | 5 |
| `single19-shape1-high21-6` | 6 |
| `single19-shape1-high21-7` | 7, 8 |
| `single19-shape1-high21-9` | 9, 10 |
| `single19-shape1-high21-11` | 11, 12, 13, 14 |
| `single19-shape1-high21-15` | 15, 16 |
| `single19-shape4-high21-2` | 2 |
| `single19-shape4-high21-3` | 3 |
| `single19-shape4-high21-4` | 4 |
| `single19-shape4-high21-5` | 5 |
| `single19-shape4-high21-6` | 6 |
| `single19-shape4-high21-7` | 7 |
| `single19-shape4-high21-8` | 8 |
| `single19-shape4-high21-9` | 9, 11 |
| `single19-shape4-high21-10` | 10, 12 |
| `single19-shape4-high21-13` | 13, 14 |
| `single19-shape4-high21-15` | 15, 16 |
| `single19-shape44-high21-2` | 2 |
| `single19-shape44-high21-3` | 3 |
| `single19-shape44-high21-4` | 4, 5 |
| `single19-shape44-high21-6` | 6 |
| `single19-shape44-high21-7` | 7 |
| `single19-shape44-high21-8` | 8 |
| `single19-shape44-high21-9` | 9, 10 |
| `single19-shape44-high21-11` | 11, 13 |
| `single19-shape44-high21-12` | 12, 14 |
| `single19-shape44-high21-15` | 15, 16 |
| `single19-shape47-high21-2` | 2 |
| `single19-shape47-high21-3` | 3 |
| `single19-shape47-high21-4` | 4 |
| `single19-shape47-high21-5` | 5 |
| `single19-shape47-high21-6` | 6 |
| `single19-shape47-high21-7` | 7, 8 |
| `single19-shape47-high21-9` | 9, 10 |
| `single19-shape47-high21-11` | 11, 12 |
| `single19-shape47-high21-13` | 13, 14, 15, 16 |
