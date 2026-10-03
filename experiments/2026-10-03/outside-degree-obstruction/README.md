```
Document:    Outside-Pair Degree Obstructions for Three Fixed Local Families
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      86df2842bc57ee17c65a14bb112030ee282fa2c5cb5bc52f6edd4b40f408896c
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Safe completion bound

Work in the regular normalized sevenfold-triple branch, with heavy triple
{1,2,3}, hub 4, the seven common blocks, and three fixed local families of
thirteen quadruples on points 4..16. The remaining eighteen blocks use only
points 4..16. Point 4 must occur in six of these blocks and every other
outside point in seven, because their already-fixed degrees are fourteen
and thirteen respectively and the completed cover is regular of degree twenty.

Let U be the outside triples not covered by any of the three local families.
For an outside pair {x,y}, let m_xy count the triples of U containing it. Each
remaining block through {x,y} covers at most three of those triples. Therefore
its outside pair multiplicity q_xy must satisfy

    q_xy >= L_xy = ceil(m_xy/3).

Summing at a point x, each outside block through x contributes exactly four
pair incidences. Hence

    sum over y != x L_xy <= 4 r_out(x),

where r_out(4)=6 and r_out(x)=7 for x!=4. A violated row proves that these
three fixed local families have no completion with the required outside
degrees. It does not exclude every family combination or a nonregular branch.

For a partial hint with a specified set of allowed global holes, remove those
holes from U before computing the bound. The same counting argument then
applies to every triple still required to be covered. Applying the full-cover
rows unchanged to partial hints would be an invalid strengthening.

# A certified obstruction in the current seed

The candidate `../first-family-independent/normalized-h14.txt` has three valid
local families of types four-hole, projective-plane, four-hole. Their two
four-hole families omit the same spoke. The candidate has eighteen outside
blocks with the regular required degrees and fourteen uncovered triples.

For a full completion of these three local families, the L_4y values for
y=5,6,...,16 are

    3, 2, 1, 2, 2, 3, 2, 2, 2, 1, 2, 3.

They sum to **25**, exceeding the available **24** pair incidences through
point 4. Thus changing only the eighteen outside blocks cannot complete this
fixed local-family combination in the regular branch. At least one local
family must change. This conclusion does not depend on point-essentiality.

`check.py` obtains the residual triples by direct subset tests, independently
computes every pair bound, and records every required third point in
`result.json`. Both full covering verifiers agree on the actual fourteen holes.
When precisely those fourteen holes are removed from the required residual,
all rows are satisfied, so the partial hint remains valid. Three malformed
input controls are rejected.

# Further hub consequences from multiplicities alone

Let h_5 and h_6 count local families omitting the two spokes. Let f_x count
local families repeating the pair {4,x}, for x=7..16. Because each local
missing graph is a matching contained in G, a family omitting a spoke has
exactly one repeat partner for point 4 among points 7..16; a family omitting
neither spoke has no repeat partner at 4. Thus sum f_x=h_5+h_6<=3.

For a spoke endpoint u, the local pair multiplicity summed across the three
families is 3-h_u. For another outside point x it is 3+f_x. A local quadruple
through a given pair covers two outside third points. Since that pair has
eleven outside third points in total, even before accounting for overlaps,

    q_4u >= ceil((5+2h_u)/3),
    q_4x >= ceil((5-2f_x)/3).

Adding the common blocks and local contributions shows that a spoke with
h_u<=1 forces final multiplicity at least six, and a repeat partner used by
at least two families also forces final multiplicity at least six.

In this regular branch the final pair-excess degree at point 4 is five. Its
three pairs to 1,2,3 each already have excess one, leaving only two excess
units for outside pairs. Consequently

    number of spokes with h_u<=1 + number of x with f_x>=2 <= 2.

In the point-essential case h_5,h_6>=1. If both equal one, the third local
family has no hole at 4. The repeat partners of the other two families must
be distinct. Both spoke multiplicities equal six, and every other outside
pair through 4 has multiplicity exactly five. The outside pair counts are
then forced: three on each spoke, one on each repeat-partner edge, and two
on the remaining eight edges. Actual overlap among the local triples can
only strengthen these bounds; the exact residual-degree rows include it.
