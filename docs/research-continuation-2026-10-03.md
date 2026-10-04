```text
Document:    C(16,5,3) Continued Research Checkpoint
Version:     v1.10.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      b380878ab82eb494759b3992f89ad98aea24d9e5aebabcc5a76c68cb018c79d2
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Research continuation

No verified 64-block cover has been found. The strongest current first-link
screen has 109 independently checked exclusions out of 258 cases in the regular
four-sevenfold branch: 27 cycle and 82 matching. The remaining 149 are open.
This is a branch result, not a global lower bound.

The six exhaustive hub-count cases exclude matching-077 in all six. Every one
of the 936 conditional records was checked against independently audited models.
Seven initial numerical failures or certificate timeouts were repaired using
the same frozen models; exact replay now confirms 419 conditional exclusions.
The other 517 records are numerically LP-optimal only. Individual conditional
exclusions do not exclude a first link unless all six hub cases are covered.

The complete surviving-template hull screen checked all 156 representatives
left by the odd-set pass. Independently replayed certificates exclude
matching-017, matching-077 and matching-083. Matching-077 overlaps the hub-count
result, so these two campaigns add three distinct first-link exclusions.
All 153 remaining LP records are fractional. Their saved primal values were
recounted using exact binary-float arithmetic; small residuals establish only
numerical feasibility, never an integer covering witness. The combined proof
ID inventory is saved in `four-seven-template-link-independent`.

The degree-19 roadmap now separately covers a sole degree-19 point and two
degree-19 points sharing either five or six blocks. The sole-point case has
38 independently audited link/high-point models; all 38 LP relaxations are
numerically optimal and fractional. The overlap-five factorization has
4,578,210 ordered union classes, with anchor reversal not quotiented. Four
sampled unions have independently audited full completion models. One sampled
union, pilot-000, is excluded by a separately replayed exact dual with gap
249957/1000000. The three other pilots each returned UNKNOWN after 300 seconds
with two solver workers and supplied no integer candidate. These four samples
do not exhaust the overlap-five branch.

The five feature rules and thirteen additional facet families were proved from
the original 100 checked exclusions and complete link classification. Their
separate LP passes did not exclude another case. Adding 8,096 independently
audited odd-set rows per model excluded matching-038 and matching-051. Separate
exact certificate replay verified gaps 8413/1000000 and 1007/200000. The complete
case accounting, certificates, source snapshots and raw model hashes are in
`experiments/2026-10-03/four-seven-blossom-screen/` and its independent audit.

All 158 earlier LP primals were inspected; none was integral and every rounded
candidate failed both covering verifiers. Four earlier 60-second integer pilots
returned UNKNOWN. Four new stronger-cut 300-second pilots also returned UNKNOWN and supplied
no integer candidate. Their complete bounded-run evidence is saved under
`four-seven-blossom-cp`.

Both complete surviving-template hull LPs were also built and independently
checked. They use all 25,020 cycle or 14,202 matching labeled links per heavy
group surviving the original 100 exclusions. Both whole-branch LPs remain
numerically feasible with fractional block values. Their two numerical primals
are stored and independently recounted; neither is a covering witness.

The completed model changes passed `uv sync --frozen`, 314 tests,
and Ruff. Three existing SWIG deprecation warnings remain. Large raw models,
full primal vectors and archived source/proof material remain in ignored scratch;
small manifests and checked evidence are kept in Git. The isolated branch has
not been merged or pushed.

## Earlier checkpoint record

The goal is still open: no verified64-block C(16,5,3) cover has been found. The best unrestricted partial cover still covers557 of560 triples. The best point-essential regular candidate still covers552. No global nonexistence claim follows from these experiments.

## Independently checked reductions

The published four-class degree19 link classification is retained. For two degree19 points sharing six blocks, all576 second links reduce to270 ordered representatives. An independent incidence-graph audit and270 explicit relabelings confirm196 classes after swapping the anchors.

Exact rational duals exclude four fixed32-block families. Every dual was replayed against all4368 possible added blocks with a standard-library checker. Independent exhaustive weighted trees exclude two more fixed families, using279 checked nodes. These are six local exclusions, leaving190 of the196 classes without such a certificate. They do not cover every degree19 configuration.

In the full regular20 branch, triples occurring six or seven times are vertex-disjoint. Sevenfold triples have an exact seven-block form, and their distinct outside hubs imply4*n7+3*n6<=16. The earlier eight-hole seeds have n7=3,n6=2, so this pattern must change before they can become full covers.

A sevenfold triple leaves three local families, each with13 quadruples on13 points and degree four at each point. A valid non-projective-plane local family was found. Two independent arithmetic enumerations show that no such family can omit both edges of the relevant two-edge star: all32235 possible Gram-matrix excess patterns have nonsquare determinant. In the point-essential branch, at least two local families must therefore omit complementary star edges.

## Recorded searches

- Four single-link runs of300 seconds,36 double-hub64 runs, and eight double-hub65 runs found no cover. The two fast double-hub negative results were subsequently checked by independent trees; all other negative solver outcomes in this batch are timeouts.
- The regular CP model with aggregate bounds retained an eight-hole seed after600 seconds. Native SAT with those bounds timed out after600 seconds. These outcomes are inconclusive.
- The first local search made41 attempts without changing a block. A second23-attempt run, with tie-breaking that favors new blocks, also kept its eight-hole seed.
- Three normalized sevenfold-triple CP runs, each300 seconds, returned UNKNOWN. Their encodings, optional heavy-count flags, fixed block IDs, pair equations and archived models passed a separate audit, including byte-identical model rebuilds.
- The longer-move heuristic still found no seven-hole qualifying state. It did find a ten-hole state satisfying the heavy-count inequality. All saved candidates were checked by both covering verifiers and a separate degree/pair/private-triple recount.

## Local families and construction searches

The local13-point classification is complete within its stated assumptions: thirteen distinct quadruples, every point of degree four, and missing pairs forming a matching. There are exactly three unmarked families, with zero, four, or six missing pairs. An independent direct enumerator found88 labelled families; a separate graph audit checked every isomorphism map. This is not a classification of all64-block covers.

In the point-essential regular branch containing a sevenfold triple, a local family omitting a chosen spoke reduces to13 first-family representatives. All44,160 labelled families have explicit checked maps to these representatives. Each of the13 full-cover CP runs timed out at20 seconds. Their models were independently reconstructed; no nonexistence claim follows.

Joint local-family and outside-block search improved from27 to14 missing triples. The next version adds exact four- and six-block trades with the projective-plane family and reached five missing triples. The best general partial still has three holes; the best point-essential regular partial still has eight. These are different search scopes.

The five-hole structured state has four disjoint sevenfold triples and one disjoint sixfold triple, an impossible pattern for a full64 cover. A checked two-outside-block point swap gives a six-hole state passing the regular heavy-count restrictions. Both covering checkers agree, all point degrees remain20, and its first family normalizes to representative r4-005. Passing these restrictions does not establish extendability.

The first-family wrapper validates every variable in a complete hint by fixing all variables in a cloned model. An explicit partial-search option removes only78 outside-pair lower bounds and one opposite-spoke condition. All13 default models remain byte-identical to their earlier versions. A27-hole strict run improved to25; a14-hole relaxed run retained14 after600 seconds. Adding residual-pair cuts retained14 after another300 seconds. Later pilots have separate frozen source/model records.

## Further conditional obstructions

Five vertex-disjoint triples, each covered at least six times, cannot include two sevenfold triples in a64-block cover. This argument does not assume regularity. All15 involved points must have degree at least20. The degree sum320 permits either all16 degrees20, or one involved point of degree21 and the remaining point of degree19. Each sevenfold triple forces a repeated outside point with three pair excesses. In either degree case, only one point can serve that role and it cannot serve twice. The full proof, independent degree/hub enumeration, and damage controls are under `experiments/2026-10-03/five-heavy-triples`.

For each outside pair, count triples through it missed by all39 local blocks. Its required outside-block pair count is at least one third of that count, rounded up. At any point, the sum of these bounds cannot exceed four times its outside-block degree. The fixed local families of the14- and five-hole seeds require at least25 at the hub, whose available sum is24. Those particular three-family combinations must change; outside-block repair alone cannot complete them.

The CP version excludes global holes from residual demand, so it remains valid for partial states. An independent checker reconstructed all364 new variables and1,105 new constraints, checked every auxiliary hint value, and rejected six damaged controls. Separate local packing cuts also passed independent audits; their120-second full-cover pilot timed out.

Repeated hubs give a further regular restriction. A sixfold triple may have at most one repeated outside point, occurring at most three times. Such hubs and sevenfold hubs must be distinct and outside all heavy triples. If h6 counts exact-six triples with a repeated hub, the refined count is3*n6+4*n7+h6<=16. The proof and arithmetic controls are in `regular-heavy-hub-bound`. The six-hole warm seed passed the earlier count filters but reused hub4, showing why those filters alone were insufficient.

The normalized hub4 cuts add325 independently checked constraints. A nine-hole hint passes those cuts and the explicit distinct-hub checks. These particular local families still fail the outside completion bound. A separate600-second heavy/residual run and an eight-worker600-second neighborhood run both retained six holes; completed run records are archived separately.

## Audit correction and current direction

A generic neighborhood repair produced another three-hole state. Its first profile summary mistakenly used a threshold of seven and omitted its sixfold triple. Root and an independent agent caught the error using direct counts and both covering checkers. The corrected state has the forbidden five-heavy-triple pattern and is not an eligible escape seed. The correction, original search records, and regression controls are retained.

Continue construction from independently checked six-hole states while allowing local families to change. The general heavy-profile heuristic made2,500,339,392 proposals in600 seconds and retained a six-hole state passing its stated profile filter; it did not find a cover. Every saved improvement passed both covering checks and an independent profile recount. Sanitizers and separate predicate/move/rollback audits passed. Ongoing campaigns remain inconclusive until a complete candidate passes both covering checkers.

At this checkpoint, frozen source passes243 tests and Ruff after `uv sync --frozen`. The scored native campaign remains active outside this checkpoint's completed evidence; it has reached a13-hole state passing its scored heavy and family-row filters and its logged sevenfold-hub diagnostics. Those checks are necessary conditions, not a covering witness or an extendability proof.

Compact certificates, source snapshots, metadata, hashes and logs are under `experiments/2026-10-03`. Large raw solver models remain in ignored scratch directories. The branch remains isolated and has not been merged or pushed.

## Four-sevenfold branch and checked linear exclusions

The full regular branch with four sevenfold triples reduces to two pair-count
patterns. Each permits 1,476 of the 4,368 lexicographic block variables. The
independent audit reconstructed both full models, their 400-variable double-triple
extensions, and all saved exact fractional witnesses. Four 300-second full-branch
CP searches returned UNKNOWN. Two specified order-four invariant subcases are
excluded by independently checked parity certificates; they do not exhaust the
branch's possible automorphisms or covers.

The first seven-block heavy link has exactly 29,970 labeled forms and 129
relabeling orbits per pair-count case. An independent enumerator checked every
form, every group operation, and all 59,940 saved relabelings. Linear screens of
all 258 representatives gave 100 independently checked exclusions: 27 cycle and
73 matching representatives. The remaining 158 are numerically LP-feasible only.
The complete proof scope, arithmetic, artifact paths and remaining cases are in
`docs/four-seven-branch.md` and `four-seven-link-screens/`.

The selected-heavy-hub repair retained its nine-hole hint. Native v1.3 now scores
shared hubs, hubs inside heavy triples, repeated exact-six hubs, and pair deficits
as soft penalties. Its two 600-second campaigns found no cover. The best saved
state passing all of those scored necessary checks has 20 holes; this is not an
improvement over the raw three-hole partial. Lower-hole states still fail known
necessary conditions.

A new six-hole partial has all holes through point12. Rebuilding only the20
blocks through that point, while keeping the other44 and requiring every added
block to contain12, needs at least22 additions by an independently checked
43/2 dual bound. The broader repair through points6 and12 timed out after300
seconds. Two feasible integer double-triple patterns also failed to yield a
cover in bounded completion searches: one timed out, and one returned solver
INFEASIBLE without an independently checked integer proof.

The completed sources passed `uv sync --frozen`,273 tests and10 subtests, and
Ruff. The three existing SWIG warnings remain. Primal inspection of the158
remaining first-link LP cases is ongoing beyond this checkpoint. Goal64 is open.

The combined-template priority screen tested the last open hub-count subcase
for each of 23 first-link representatives. It produced one new independently
replayed certificate: matching-032 at (m4,z)=(0,1), gap 7651/1000000. Together
with its five previously checked hub cases, this excludes matching-032 entirely
within the regular four-sevenfold branch. The 22 other priority LPs remain
numerically optimal and fractional. This brings the combined total to 106
excluded first links and 152 open; it supplies no covering witness.

A separately audited catalog refresh uses all 106 checked exclusions. It removes
1,512 matching templates per heavy group, leaving 12,690 and 55,528 total model
variables. The cycle catalog and matrix are byte-identical to their originals.
Direct re-enumeration, exact row reconstruction and 16 damaged controls passed.
The 106-catalog build was audited before the later solver runs below.

## Refreshed hull and integer construction wave

The 106-catalog matching screen added two independently replayed exclusions:
matching-095, gap 22563/1000000, and matching-113, gap 44/15625. The checked
union is now 108 of 258, with 102 cycle and 48 matching first-link cases open.
A further audited refresh removes 648 templates per group, leaving 12,042
matching templates and 52,936 columns. Its whole-branch LP and all 48 fixed-link
LPs returned numerical OPTIMAL, with fractional primals and no further exact
exclusions. This is a numerical stopping point for this pruning procedure;
it does not prove integer feasibility or settle the branch.

The equivalent Boolean-template CP models, built from the frozen 106 catalog,
retain all original 4,768 variables and 4,270 constraints and add exactly one
selected template per group with 276 heavy-block marginal equalities. Separate
model reconstruction rejected 20 damaged controls. Matching and cycle pilots
requested 300 seconds and eight workers each; both returned UNKNOWN without
candidates. Recorded wall times were 301.523 and 300.277 seconds.

A separate SCIP pilot used the same matching hull with continuous template
weights. Binary heavy-block marginals force a unique selected template, so this
has the same integer projection. The independent model audit rejected 19
damaged controls. SCIP reached its requested 300-second time limit after
304.86 solver seconds, with eight nodes and zero solutions. NOT_SOLVED remains
inconclusive; no solver-only negative result is counted as an exclusion.

The new native sole-degree-19 heuristic freezes one complete 19-block link and
uses degree-preserving moves on the other 45 blocks. Four 300-second pilots
ended with 17, 17, 20 and 18 holes after 1,061,025,966 proposals. All 264 saved
states were recounted independently; both covering verifiers agreed they were
incomplete. The 60 saved operations and rollbacks passed replay. These are
partial states in a stricter degree profile, not improvements over the existing
unrestricted three-hole near-cover. Sanitizer checks and malformed-input
controls passed. Required package validation again passed all 314 tests and
Ruff, with the same three SWIG warnings.

Two prepared narrower CP pilots fix matching-029/(m4,z)=(0,2) and
matching-063/(0,1). Their independent audit reconstructs exactly nine added
rows, preserves the full base protobuf, checks the five other excluded hub
cases for each, and rejects 16 damaged controls. Both returned uncertified INFEASIBLE: 27.931 seconds for matching-029 and
37.414 seconds for matching-063. No witness was emitted; neither solver report
is counted as a checked exclusion.

## Whole-template construction and proof translation

The checked first-link union remains 108 of 258. Rechecking the two surviving
hub subcases with the stronger 108-catalog LP still returned fractional numerical
OPTIMAL, with no certificate or covering witness.

A new native search changes all seven blocks of a heavy link in one move and
changes ordinary blocks with degree-preserving trades. The complete audited
108 catalogs supply four mutable heavy templates, alongside 36 ordinary blocks.
Rotation is used only to build starting seeds. All later moves can break it.
Two 300-second single-worker pilots ended at 21 holes (matching) and 19 holes
(cycle), after 427,559,166 proposals in total. All 144 saved pilot states and
32 operation traces passed independent recount and the required covering checks;
none is a cover. The best pair-target L1 defects were 30 and 24, and both states
had nonheavy triple multiplicity three, motivating a separate soft-score variant.

Two seed-master MIPs kept only the 276 allowed heavy-block variables integral.
The full template-hull master timed out after a 60-second budget at one node;
the sparse base-row master timed out after a 30-second budget at 27 nodes.
Neither returned a heavy pattern or covering witness. Their fractional ordinary
variables mean even a feasible master would still need integer completion.

The two restricted CP models were translated to CNF for separate proof-producing
search. Root independently reconstructed every clause and auxiliary boundary,
verified the full source-audit chain, checked 1,189 small signed/weighted rows on
4,756 assignments, and rejected six damaged clause fixtures. The translation
gate covers 7,531,645 clauses across both models. It proves encoding equivalence
only; the proof-producing searches and proof-check results remain separate work.

## First checked integer exclusion and new construction pools

Matching-029 is now excluded in all six hub cases. The last case, (0,2), has a
CaDiCaL proof accepted by the separate pinned DRAT-trim checker. Root replayed
the binding and the other five exact rational certificates, including all
model, CNF, proof, tool and log hashes. The immutable new union has **109 checked
first-link exclusions and 149 open**, comprising 102 cycle and 47 matching.
This remains only the regular four-sevenfold branch. The saved native solver
time for the new case is 192.38 seconds; a lost Python timing receipt remains
unknown. The first matching-063 proof run timed out and is not an exclusion.

The first soft-score template pilots preserve all original legal moves and
score holes, pair-target errors and nonheavy overcoverage separately. Matching
reached 17 raw holes (score 116), with a separate score-best at 19 holes (106).
Cycle reached 12 holes with score 92. All 118 saved states and 32 move traces
were independently recounted and checked by both covering verifiers; no cover
was found. A longer cycle continuation uses a new immutable run and the same
audited source, catalog and score.

A source-backed filter-and-fan search tried linked block-replacement paths from
the unrestricted three-hole seed. All twelve approved 30-second runs stayed at
three holes. Their 290,295 saved traces/moves and all best witnesses were checked.
The paired policies differ in acceptance as well as branching, so this is not
an isolated measurement of beam width. The large raw traces stay outside Git.

Two independent finite-field constructions agree on the Steiner 3-(17,5,1)
design, its 48 finite circles and 20 four-point affine lines. The pool containing
those circles and all 240 line extensions has 288 five-point blocks. Its exact64
pilot returned UNKNOWN after 60.006202 solver seconds. A broader pool contains
all 288 five-point caps and the 240 line extensions. Its 528-variable model and
separate necessary point/pair cuts passed independent reconstruction and damaged
controls. The broader incidence-cut construction pilot returned UNKNOWN after 300.02201 solver seconds with eight workers. No witness or exclusion resulted.

A smaller matching-063 CNF also passed independent deduction and clause checks:
2,928 row-reason steps establish 15,663 Boolean values; substitution preserves
all original constraints and reduces the CNF to 2,285,639 clauses. This is an
equivalent restricted encoding, not an infeasibility proof. Its new bounded
binary-proof pilot and separate certificate check remain active work.

## Completed continuation and construction diagnosis

The unchanged 600-second cycle continuation made 490,972,432 proposals and 981
restarts. Both best states remained the same 12-hole, score-92 seed. All 40
saved states and 16 operation records passed the independent audit and both
covering checkers confirmed their positive deficits. These are checked partial
states, not covering witnesses.

Fixing only that seed's 28 heavy blocks leaves all 36 ordinary choices free.
The independently reconstructed completion model returned CP-SAT INFEASIBLE in
presolve (0.014561 solver seconds, one worker, seed 2026104101). This solver
response alone is not a proof certificate; the diagnosed scope is this one
heavy-template combination.

A new finite counting check excludes choosing exactly one extension of each
affine line while retaining at most 46 of the fixed 48 circles. Every pair of
removed circles has a conflicting secant line, verified over all 1,128 pairs.
Thus that specific construction subcase needs at least 67 blocks. This does not
extend to multiple extensions per line or to the unrestricted covering problem.
See `affine-single-extension-obstruction` for the argument and complete audit.

The checkpoint passed `uv sync --frozen`, all 314 tests (three existing SWIG
warnings), and Ruff. The 64-block target remains open. The best unrestricted
partial still misses three triples.

The cycle-heavy conflict now has a separate finite certificate, independently
replayed from seven supporting blocks. All 18 allowed ordinary blocks that
could cover `(3,11,15)` exceed a forced anchor-pair excess budget. This proves
that this heavy tuple cannot complete within the degree-20 family, without
assuming hub-to-hub pair counts. It does not exclude a full first-link case.

A second independent geometric count checks all 1,712,304 five-circle omissions
in the fixed 48-circle pool. With exactly 21 extensions, the maximum incidence
capacity is 46 versus the required 50. Thus both the 20-extension and
21-extension subcases are excluded for a 64-block cover in that pool. The
six-family construction and all other unrestricted families remain open.

## Anchor-only lookahead and completed geometric screens

The new native variant penalizes heavy tuples having an uncovered triple that
no individually admissible ordinary block can cover. Its admissibility rule
uses only forced anchor-touching pair excess budgets; hub-pair targets remain
soft. Independent fresh-tuple, score, rollback, cache-eviction and sanitizer
checks passed before the single 300-second cycle pilot.

That run improved the structured seed from 12 to 10 holes, score 78, with zero
unsupported triples. It made 72,308,652 proposals and 144 restarts, exercising
170 cache clears. All 54 saved states and 16 operation records passed the
independent metric audit and both cover-verifier consistency checks. The best
state is still incomplete. The unrestricted best remains three holes.

A separate 1,200-variable, 577-row model fixes only this new tuple's 28 heavy
blocks and chooses any 36 ordinary blocks, with no fixed hub graph. Root
reconstructed every row and rejected six damaged models before its diagnostic.

In the geometric pool, the complete fixed-circle capacity screens for 22, 23
and 24 extensions checked 1,533,939; 10,737,573; and 62,891,499 deletion sets.
Their maxima are 55, 66 and 75 versus requirements 60, 70 and 80. An independently
replayed transitive action justifies fixing one omitted circle. Explicit linear
maps transfer these exclusions to each individual circle family. They do not
apply to the union of six circle families or the unrestricted block universe.

A much smaller 69-row necessary relaxation returned UNKNOWN after 60.002797
solver seconds, with one worker, and supplied no candidate. Six separate
10-second capacity annealing pilots for nine through fourteen omitted circles
found maxima 84, 93, 102, 111, 120, 129, below the required 90, 100, 110, 120, 130, 140.
These are heuristic records, not exhaustive upper bounds. All 16 sets consisting
of the fifteen circles through one point have exact capacity 138 at 31 extensions,
also below the requirement 150. No capacity survivor was available for the
prepared exact extension-completion builder.

The hub-unrestricted fixed-heavy diagnostic returned UNKNOWN at its 60-second,
one-worker limit (seed 2026104401), with no candidate. Independent recount of
the frozen ten-hole tuple confirms 680 admissible ordinary blocks and zero
unsupported triples. This does not establish that the tuple can be completed.

## Checked completion obstruction

The stronger fixed-heavy LP returned an exact rational separating certificate.
Root independently reconstructed the strengthened model and replayed all 531
signed rows against all 1,200 ordinary columns. The weighted lower bound is
10629/1000, while the maximum over the unit box is 87/1000, leaving a positive
gap 5271/500. Five damaged certificates were rejected.

This proves that the ten-hole state's fixed 28 heavy blocks cannot complete in
the regular four-sevenfold family, even with every hub graph allowed. It does
not exclude a complete first-link representative or change the 109-entry
first-link exclusion union. A reusable inequality in variable heavy patterns
has not yet been derived or audited.
