```
Document:    Degree Budget for Disjoint Sixfold and Sevenfold Triples
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      4715d182624ebceaf56058445cce6b24be8838c05cb83fbd4aae6f776f83bc3a
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Conditional theorem

Suppose a full C(16,5,3) covering has b blocks and contains q vertex-disjoint
triples of multiplicity at least six, with n7 of these triples having
multiplicity at least seven. For 0 <= n7 <= q <= 5,

    b >= ceil((304 + 3q + ceil(2n7/3))/5).

In particular, if q=5 and n7>=2, then b>=65. Thus a 64-block cover containing
five disjoint sixfold-or-heavier triples can have at most one sevenfold-or-
heavier triple among them. No regularity assumption is used. This is a
conditional obstruction to a structural profile, not an unconditional lower
bound of 65 for C(16,5,3). No novelty claim is made.

# Proof for arbitrary b

For a pair p, let lambda(p) count its containing blocks. Full triple coverage
implies lambda(p)>=5, since each such block covers only three of the fourteen
possible third points. For a point x of degree r_x, summing pair multiplicities
through x gives 4r_x. Consequently

    r_x >= ceil(75/4) = 19,
    E_x = sum over y != x (lambda(x,y)-5) = 4r_x-75.

These facts hold for every full covering, including b>64.

For a triple T of multiplicity mu, any one of its pairs p already uses mu
incidences of the same third point. Covering all thirteen other third points
therefore requires

    3 lambda(p) >= mu + 13.

If mu>=6, then lambda(p)>=7. Every point of one of the q selected triples
has two such internal pairs, contributing at least four to E_x. Hence each
of these 3q points has degree at least twenty.

Use baseline degree twenty on the 3q selected points and nineteen on the
remaining points. Write delta_x for each point's nonnegative integer degree
above its baseline. The total surplus is

    s = sum delta_x = 5b - (20*3q + 19*(16-3q)) = 5b-304-3q.

For each of the n7 triples choose seven containing blocks. Their fourteen
outside incidences lie on thirteen points, so some outside hub d occurs at
least twice. If a is any point of that triple, the pair {a,d} occurs with
each of the other two triple points at least twice. Covering all fourteen
third points then requires 3 lambda(a,d)>=16, hence lambda(a,d)>=6.
Each chosen hub must therefore supply three distinct positive-excess edges
to its triple.

If a point x serves as hub for k_x selected sevenfold triples, those 3k_x
edges are distinct because the triples are disjoint. If x belongs to a
selected triple, it cannot be hub for its own triple, so these hub edges
are also distinct from its two internal pairs. After reserving four excess
units for those internal pairs, at most

    (4*(20+delta_x)-75)-4 = 1+4delta_x

remain. If x is outside all selected triples, its entire excess budget is

    4*(19+delta_x)-75 = 1+4delta_x.

In either case,

    k_x <= floor((1+4delta_x)/3) <= 3delta_x/2.

The second inequality is immediate for integer delta_x=0 or 1; for delta_x>=2
it follows from (1+4delta_x)/3 <= 3delta_x/2. Summing over all points yields
n7=sum k_x<=3s/2. Since s is an integer, s>=ceil(2n7/3). Substitution in
s=5b-304-3q proves the bound, without restricting b to 64.

# The 64-block, five-triple case directly

Fifteen selected points have degree at least twenty and the remaining point
has degree at least nineteen. Their total is 320. The only possibilities are:

* Every point has degree twenty. A hub inside another selected triple would
  need at least seven excess units (four internal and three hub edges), but
  has only five. Only the remaining point can be a hub, and its five excess
  units cannot support two disjoint triples.
* One selected point has degree twenty-one, the remaining point has degree
  nineteen, and all other points have degree twenty. Only the degree-twenty-one
  point can be a hub. Its nine excess units, after reserving four internal
  units, cannot support two triples. Moreover its own selected triple cannot
  be sevenfold because that triple would need a different eligible hub.

This gives the same at-most-one conclusion directly.

# Candidate and independent controls

The saved 64-block, three-hole candidate
`../heuristic-tabu-2026100301-deficit-3.txt` has the five disjoint heavy triples

    (1,3,6):7  (2,14,15):6  (4,8,10):7  (5,13,16):7  (9,11,12):7.

Its missing triples are (2,7,14), (2,7,15), (7,14,15). It is not a full cover,
so it is not a counterexample. Every repair to a full 64-block cover must
change this heavy-triple profile: either reduce one of the five triples below
six or leave at most one of them at seven or more. The theorem does not say
that the candidate cannot lead to a solution after such a change.

`check.py` independently enumerates all sixteen possible full-cover degree
profiles in the q=5,b=64 case, all ten choices of two sevenfold triples, and
all 13^2 legal hub assignments. For each of the 27,040 combinations it forms
the required internal and hub edge union and tests every vertex's pair-excess
budget. None passes. A one-sevenfold regular profile and a two-sevenfold
65-block degree-budget profile serve as positive controls for the arithmetic
test; they assert only consistency of the necessary edge budgets, not actual
covering constructions. The script also checks the saved candidate by direct
counting and both covering verifiers, and exercises damaged input controls.
