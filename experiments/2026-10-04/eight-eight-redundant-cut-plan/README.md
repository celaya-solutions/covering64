```text
Document:    Optional Eight Plus Eight Redundant Cut Plan
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      68ddc4e6b1cc9f0658d2e73f8bf465faa3c4341cb1d85f1c0d9fe0a33b7803a9
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Optional redundant cuts for the 8+8 recipe

These deductions are complete counting proofs within the three prepared
recipes AA, AB and BB. They assume the existing one-extension-per-base rules
and all triple-cover rows. They impose no new restriction on those recipes,
but do not apply as reductions of the unrestricted covering problem. The
frozen sources and models are unchanged. No solver was run.

## Notation and pair cuts

Fix a target half H. For its internal pair P, q_P is the number of selected
quadruples containing P. Let X_P count opposite-half residual triple bases
extended by P. For a point a in H, let p_a=sum_{P containing a} X_P and let
s_a count opposite-half quadruple bases extended by singleton a. The base
rules give sum_P X_P=24, sum_a p_a=48 and sum_a s_a=8.

The six internal triples through P include two per selected quadruple. Thus
exactly 6-2q_P residual triples contain P, and its final block multiplicity is
q_P+(6-2q_P)+X_P=6-q_P+X_P. A pair must occur at least ceil(14/3)=5 times in
any full cover. Therefore the following row is redundant:

`X_P >= max(q_P-1, 0)`.

For type A, four pairs have q=0 and the other 24 have q=2. The latter require
at least 24 extension occurrences and only 24 exist. Therefore every q=2 pair
has X=1 and every q=0 pair has X=0. The q=0 pairs form a perfect matching M.
The 24 residual triple bases on the opposite half must be assigned bijectively
to the 24 pairs of K8 minus M. Each target point consequently has p_a=6.

For type B, the histogram is q=1 on 12 pairs, q=2 on 12 pairs and q=3 on four
pairs. Its mandatory load is 20. Write z_P=X_P-(q_P-1). Then z_P>=0 and
sum_P z_P=4. These four extra edge occurrences form a multigraph, with degree
e_a=sum_{P containing a} z_P. The baseline graph has degree five at every
point, so p_a=5+e_a, sum_a e_a=8 and 0<=e_a<=4.

## The point cut forces type A to be regular

Every point lies in four local quadruple bases and nine local residual triple
bases, so its final degree is r_a=13+p_a+s_a. Count triples consisting of a
and a pair entirely in the other half. The nine local triple bases contribute
nine incidences; the p_a opposite triple bases contribute three each; the
s_a opposite quadruple bases contribute six each. Covering all 28 pairs gives

`9 + 3*p_a + 6*s_a >= 28`, equivalently `p_a + 2*s_a >= 7`.

The equivalence uses integrality: 3*(p_a+2*s_a)>=19. This is a separate
redundant row per point, without any auxiliary variables.

For type A, p_a=6 forces s_a>=1. Since eight s_a values sum to eight, every
s_a=1 and every r_a=20. Consequently the eight opposite quadruple bases must
be assigned bijectively to the eight target points. In particular, the four
quadruples through any point of the opposite half have four distinct singleton
extension labels. AA is necessarily regular degree 20 on all 16 points; AB
is necessarily regular on its type A half. The target half's type determines
these conclusions, regardless of the opposite half's type.

For type B, the point row becomes e_a+2*s_a>=2 and r_a=18+e_a+s_a. A degree-19
point requires e_a+s_a=1, so its only possible case is e_a=0, s_a=1. The other
integer possibility e_a=1, s_a=0 violates the point row. This does not rule
out degree-19 points in type B or force its singleton assignments to be a
bijection.

As a consistency check, the sum of internal-pair counts through a is 30+p_a.
Subtracting it from 4*r_a gives cross-pair excess degree
`3*p_a+4*s_a-18`. It equals four in type A and equals
`-3+3*e_a+4*s_a >= 1` in type B. Both halves have total cross-pair excess 32.
The opposite-pair incidence excess at a is `3*p_a+6*s_a-19`: five in type A,
and `3*e_a+6*s_a-4` in type B. Its sum is 40 on either half.

## Optional triple upper bounds and exact row plan

For a type A internal pair with q=2, its block multiplicity is five. Those
five blocks supply 15 triple incidences through the pair. Six are the six
internal triples, each covered once. Thus its eight mixed triples have nine
incidences in total. Since each is covered, exactly one has multiplicity two
and seven have multiplicity one. Each therefore admits the redundant upper
bound two. There are 24*8=192 such mixed triples per type A target half.
For a matching pair q=0, the analogous total is 12 and each mixed multiplicity
is at most five. In type B the corresponding totals are 9+3*z_P, so a mixed
triple multiplicity is at most 2+3*z_P; z_P=0 gives the same one-double pattern.

A future v2 may add the following, while retaining all original cover rows:

- Per type A target half: fix the 24*4=96 forbidden pair-extension variables
  to zero; impose X_P=1 on its 24 allowed pairs; impose s_a=1 at all eight
  points. The explicit point-degree-20 rows would then be optional duplicates.
- Per type B target half: add the 16 nonzero pair-floor rows (12 at least one,
  four at least two), plus the eight rows p_a+2*s_a>=7. The 12 q=1 pair-floor
  rows are tautologies and may be omitted.
- Optionally add the 192 mixed-triple upper bounds of two per type A half.
  These do not replace the existing lower cover bounds.

The type A zero fixes reduce the eligible pools from 1,472 to 1,280 for AA,
1,376 for AB and leave BB at 1,472. All variable IDs may remain in the original
4,368-column lexicographic order, with domain fixes only. These are optional
future edits; this plan neither edits nor launches any model.

[check.py](check.py) independently reconstructs both base recipes, checks all
pair/point counts, tests the rounded inequality on 441 integer pairs, and
checks all 6,435 singleton-count compositions of eight. It finds exactly the
all-one type A vector and verifies the type B degree-19 condition. The full
receipt is [checks.json](checks.json). These necessary facts yield no
contradiction and are not a feasibility test of the construction.
