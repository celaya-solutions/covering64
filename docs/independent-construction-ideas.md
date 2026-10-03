```text
Document:    Independent Construction Routes for C(16,5,3)
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      8c02fdb3f20328d091629e85988e8b170e48c54dbf012add011508eaca03e1b4
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Scope and recommendation

The saved checkpoints still report no verified 64-block cover. The known
65-block cover and the 557/560 partial cover are not new evidence from this
note. The reconstructed history in `docs/recovery.md` remains the authority on
which older artifacts are missing.

Three structurally different restricted routes are available:

| Route | Restricted feature | Cheap first test |
| --- | --- | --- |
| Folded five-cube pair profile | Pair multiplicity six on the 40 edges of srg(16,5,0,2), five elsewhere; point degrees 20 | Audit the excess equations, then the root agent's bounded all-block model |
| Eight-pair excess support | Every triple meeting three different pairs is covered exactly once; no point-degree assumptions | All 4,368 variables with 448 equality and 112 covering constraints |
| Shortened inversive plane | Blocks selected from 48 circles and 240 extended affine lines | Independently audit the mother geometry; reject the saturated simple family without a solver; optionally search the full 288-block pool |

The eight-pair model is the preferred second solver direction. It places excess
on a different set of triples than the folded-cube model, and it does not fix
a point link, a high-multiplicity triple, or an invariant block family. None of
these restrictions is a complete reduction of unrestricted C(16,5,3).

## Eight pairs: exact transverse coverage

Fix the groups G_i={2i+1,2i+2}, for i=0,...,7. There are
C(8,3)*2^3=448 transversal triples, with one point in each of three groups.
The other 8*7*2=112 triples contain one complete group.

Use all 4,368 five-subsets in the package's existing lexicographic order.
For Boolean block variables x_B, impose

* sum_B x_B=64;
* sum_(B contains T) x_B=1 for each transversal T;
* sum_(B contains T) x_B>=1 for each nontransversal T.

Thus all 80 excess triple occurrences lie on the 112 nontransversal triples.
This is a restriction on where overlap occurs, not on block orbits or on point
degrees. The fixed pair labels lose no possibilities *within the family of
covers that admit such a partition*, because any partition into eight pairs
can be relabeled to this one. That does not show that every cover admits one.

Every five-block has exactly one of the following group patterns:

| Pattern | Available blocks | Transversal triples per block | Other triples per block |
| --- | ---: | ---: | ---: |
| 2+2+1 | C(8,2)*6*2=336 | 4 | 6 |
| 2+1+1+1 | 8*C(7,3)*2^3=2,240 | 7 | 3 |
| 1+1+1+1+1 | C(8,5)*2^5=1,792 | 10 | 0 |

If a,b,c count these three types, then exact transversal coverage and 64 blocks
give 4a+7b+10c=448 and a+b+c=64. Consequently 2a+b=64 and c=a.
These are derived equations. In particular the selected blocks contain 64
complete group occurrences, averaging eight occurrences of each paired edge.
This differs sharply from the folded-cube profile's pair multiplicities five
and six.

The optional `balanced_types=True` subfamily sets b=0, hence a=c=32. It retains
all 4,368 variables but forces the 2,240 variables of the middle type to zero.
It is narrower than the main paired model and must be reported separately.

For a fixed triple of groups, its eight transversal triples form a binary
three-cube. A 2+2+1 block covers one of its six coordinate halves. Two halves
with different singleton-group directions overlap in two triples, so their
blocks cannot coexist under exact coverage. Two such blocks can coexist only
as complementary halves in the same direction. This is a useful independent
local consistency check and a possible redundant cut, not an extra assumption.

`scripts/independent_pair_partition.py` implements the model and an optional
single-worker runner. Its default budget is 120 seconds and seed 640303. It
saves the source snapshot, model, solver log, versions, revision and hashes.
A returned witness is passed through both project cover verifiers and a
separate recount of the partition restriction. The authoring subagent has not
run a solver. The root agent owns scheduling to avoid overlapping workers.

## Shortening the order-four inversive plane

Work in F_16=F_2[a]/(a^4+a+1), with polynomial-basis integers 0,...,15 mapped
to point labels 1,...,16. Its subfield F_4 is the set of roots of z^4=z.
The norm is N(z)=z^5, taking nonzero values in F_4^*.

For every center c in F_16 and radius r in F_4^*, define the five-point circle

    C(c,r)={z : N(z-c)=r}.

There are 48 circles. The affine lines are the 20 distinct four-sets

    L(c,d)={c+d*u : u in F_4}, d nonzero.

These are the blocks obtained by deleting infinity from the usual 17-point
inversive plane: the circles remain five-blocks, and its infinity-containing
blocks become affine four-lines. More importantly, the claimed property is
directly checkable without trusting the name of the construction:

    48*C(5,3)+20*C(4,3)=480+80=560,

and each of the 560 triples occurs exactly once in this mixed collection.
Every circle is an affine oval: it has no three collinear points and exactly
ten secant lines. Its center is its unique nucleus, lying on no secants.
Every other exterior point lies on two secants, and each circle point lies
on four secants.

### Exact obstruction for one extension per line

Consider covers made from a subset of the 48 circles and exactly one block
L union {p_L} for each of the 20 lines, with p_L outside L. If a circle C is
removed, none of the retained circles covers one of C's ten triples, since
the original mixed collection partitions triples. An extended line covers
at most one triple of C. Such a triple requires L to be one of C's ten
secants and p_L to be a third point of C. Therefore **all ten secants must
serve C**, with each serving a different triple.

Any two distinct circles C,D have a common secant L with C intersection D
contained in L. The assertion has three elementary cases:

* If they meet twice, take the line through their two common points.
* If they meet once at p, each has four secants among the five lines through
  p. At least three of those lines are common secants; any one works.
* If they are disjoint, take a point of D other than C's nucleus. At that point
  two lines are C-secants and four are D-secants. Among five lines, the two
  sets overlap. Since C,D are disjoint, the required containment is automatic.

The chosen line cannot serve both circles: a common extension point would
need to be in (C intersection D) minus L, which is empty. Thus at most one
circle can be removed. This proves a lower bound of 67 **only for the family
with exactly one extension per affine line**.

The bound is attained. Label the points of one removed circle 0,...,4 and
pair its ten pair-indices as

    01|23, 02|14, 03|24, 04|13, 12|34.

For each paired pair, extend both secants by the remaining fifth circle
point. These ten choices cover the circle's ten triples exactly once. Extend
the other ten lines arbitrarily and retain the other 47 circles. The result
has 67 distinct blocks. This is a control construction, not an improvement
over the known 65-block cover.

The standard-library checker at
`experiments/2026-10-03/independent-geometry/check_inversive.py` constructs the
field and blocks independently. It checks exact triple ownership, all oval
secant counts, all 1,128 circle-pair obstructions, duplicate/malformed/damaged
controls, and the explicit 67-block cover. Its JSON includes hashes of the
geometry, the full 288-block pool and the obstruction witnesses, as well as
the 67-block witness. The project verifiers must additionally check that
witness. The root agent executed it and saved `inversive-audit.json` in the
same directory. That report checks all 1,128 pairs (168 disjoint, 240 meeting
once, 720 meeting twice), all 560 original triples and all three negative
controls. The subagent read that saved report; solver work remains with root.

### The larger 288-block test remains open

Allow any number of extensions per line and use the block pool consisting of
48 circles plus all 20*12=240 extended lines. These blocks are distinct.
Use a variable y_C for each circle and z_(L,p) for each extension. The exact
restricted feasibility model for 64 blocks is

    sum_C y_C + sum_(L,p) z_(L,p) = 64;
    sum_(p outside L) z_(L,p) >= 1, for each of 20 lines;
    y_(C(T)) + sum_(the three pairs e in T) z_(L(e), T minus e) >= 1,
        for each of 480 noncollinear triples T.

The final sum has exactly three terms: each pair of T determines its affine
line and the remaining point is the extension. Hence this is only 288 Boolean
variables and 500 covering constraints, with no fixed retained circle count.
If m circles are removed, the number of selected extensions is m+16. Covering
all 20 lines requires m>=4, and the preceding obstruction excludes m=4.
Counting noncollinear triple incidences gives

    10m <= 6(m+16), hence 5 <= m <= 24.

A plain fractional relaxation is not a useful rejection screen. The symmetric
assignment y_C=3/4 and z_(L,p)=1/12 covers every triple exactly once and has
objective 56, matching the elementary 560/10 counting bound. At objective 64,
the assignment y_C=17/24 and z_(L,p)=1/8 is feasible: its collinear coverage is
3/2 and its noncollinear coverage is 13/12. Affine field maps act transitively
on points and on pairs, so this assignment has point incidence 20 and pair
incidence 16/3. It survives the usual degree-at-least-19 and pair-at-least-five
inequalities. Integer search or stronger combinatorial cuts are needed.

`scripts/independent_inversive_search.py` implements this domain as all 4,368
lexicographic variables with each of the 4,080 outside-domain variables fixed
to zero, 560 ordinary covering inequalities and the 64-block count. Its
single-worker runner defaults to 120 seconds and seed 640304, saves both
source files and the exact domain with hashes, and checks any witness with
both cover verifiers. No point-degree or symmetry conditions are added.

A bounded run on this pool would be genuinely different from the saved
60-block-core neighborhoods, although any successful result must still be
checked for accidental overlap with that core and by both covering verifiers.
A failed search says nothing about five-blocks outside this pool. Even a
certified infeasibility result would exclude only this pool.

## Sources and evidence boundaries

* Consulted on 2026-10-03:
  <https://www.win.tue.nl/~aeb/graphs/Clebsch.html>, the graph page maintained
  by Andries E. Brouwer. It gives the folded five-cube parameters (16,5,0,2),
  the four-cube-plus-antipodes construction, automorphism-group order 1,920,
  and the equivalent F_16 construction using nonzero cube differences.
  Brouwer calls this graph the **complement** of the Clebsch graph, and warns
  that naming differs across authors. Always state the parameters.
* The same page cites J. J. Seidel, *Strongly regular graphs with (-1,1,0)
  adjacency matrix having eigenvalue 3*, Linear Algebra and its Applications
  1 (1968), 281-298. The original paper was not independently read here; its
  contents are not being used as checked evidence.
* Bibliographic metadata only was checked at
  <https://api.crossref.org/works?query.title=finite%20inversive%20planes%20Bruck&rows=5>.
  It identifies P. Dembowski and D. R. Hughes, *On Finite Inversive Planes*
  (1965), <https://doi.org/10.1112/jlms/s1-40.1.171>. No theorem from its
  unavailable full text is assumed. The order-four construction and the
  restricted obstruction above are instead fully specified for independent
  reconstruction.
* The paired-partition equations are direct counts, not claims of a published
  construction or a new theorem. Their feasibility is not known from this
  note. The root subsequently tested the288-block pool for120 seconds with one
  worker and seed640304; it returned UNKNOWN, which is inconclusive.

No researcher was contacted, and no claimed discovery was published. Solver
UNKNOWN or a time limit is inconclusive. Solver INFEASIBLE alone is not an
independently checked theorem, even for these restricted families.
