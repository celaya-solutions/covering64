```text
Document:    Independent Degree Nineteen Roadmap Review
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      80ea47d2fa30a3bb77d957e4a8f1717bb9bc9f6f37c10181600b37fa647a01b3
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent result

The roadmap's 38 sole-degree-19 cases and 34 overlap-five anchor cases pass
an independent audit. Full first-link automorphism groups were recomputed
from the nineteen blocks themselves, without using the supplied groups to
prune the enumeration. Group orders are 4, 2, 2 and 4 for shapes 1, 4, 44
and 47. Their point-orbit counts are 8, 11, 10 and 9. Removing the unique
sixfold neighbor leaves 7, 10, 9 and 8 fivefold-neighbor orbits.

`check.py` validates every witness block, all outside pair coverage, every
source hash and all case IDs. Its exhaustive bijection search prunes only
by singleton, pair, triple and quadruple incidence counts, each necessarily
preserved by an automorphism. Every completed map preserves the full block
set. The independently obtained maps equal the supplied groups exactly;
union-find independently recovers the point orbits. The four searches visit
52, 38, 34 and 102 nodes. `audit.json` records every resulting permutation.

# Completeness of the degree split

For any point p, each other point q occurs with p in at least five blocks:
fourteen triples through the pair must be covered, and one block through the
pair covers only three. Summing these pair incidences gives `4*r(p) >= 15*5`,
so every point degree is at least 19.

If no point has degree 19 and the cover has at most 64 blocks, then all sixteen
degrees are at least 20. Their sum is five times the block count and at most
320. Equality follows, giving exactly 64 blocks and degree 20 at every point.

If precisely one point has degree 19, the degree sum is at least
`19 + 15*20 = 319`. It is a multiple of five and at most 320, so it equals
320. Exactly one other point has degree 21 and the remaining fourteen have
degree 20. This case does not assume a second degree-19 point.

If a point p has degree 19, its fifteen pair multiplicities sum to 76 and are
each at least five. Therefore exactly one neighbor has pair multiplicity six
and the other fourteen have multiplicity five. For any chosen second
degree-19 point q, the two point links share exactly five or six blocks.
These cases together with the sole-degree-19 case cover the degree-19 branch.
When several choices of p and q exist, cases can overlap; disjointness is not
needed for existence-preserving search.

# Extending smaller covers

With two selected degree-19 points, any cover of m <= 64 distinct blocks can
be extended to 64 while leaving both selected degrees unchanged. Add unused
blocks avoiding both points. There are `C(14,5)=2002` such blocks, at most m
already selected, and only `64-m` additions needed. Since `2002-m >= 64-m`,
enough distinct choices always exist. Adding blocks preserves coverage.
Both chosen point links, their overlap and their degrees stay unchanged.

The sole-degree-19 case is already forced to have exactly 64 blocks. Thus
the extension argument never assumes that a sole-degree-19 cover has a
second degree-19 point. For overlap five, the fixed union has `19+19-5=33`
blocks and an exact-64 completion needs 31 additions avoiding both anchors.
For overlap six, the corresponding counts are 32 and 32.

# Symmetry scope and prerequisites

After fixing the first point link, a valid full-link automorphism may relabel
the entire cover and send a distinguished point to its orbit representative.
This preserves existence and places no invariance requirement on the cover.
All high-point orbits, including the unique sixfold neighbor, are retained in
the sole-degree-19 case. The overlap-five case retains exactly the orbits whose
pair multiplicity with the first anchor is five.

The separate exhaustive classification into four point-link classes remains
a prerequisite; this audit does not repeat that classification or prove that
any completion exists. It introduces no new restriction on unrestricted
covers, beyond the stated case analysis, and produces no global bound.

The residual-pair observation also checks out: for m=1 or m=2 appearances of
an outside pair in the fixed first link, the required additional count is
`ceil((13-2*m)/3)=5-m`. This repeats the existing pair bound and is not a
stronger cut. A graph blossom inequality cannot automatically be applied to
three-element residual edges.

# Replay

Run `uv run python experiments/2026-10-03/degree19-roadmap-independent/check.py`.
The checker performs no optimization. Input witnesses and automorphism data
are in `../link-classification`; the audited roadmap is `../degree19-roadmap`.
