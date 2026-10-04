```text
Document:    C(16,5,3) Continued Research Checkpoint
Version:     v1.28.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      beed0259818bcd313c74802ad360609f35ef075d703a3b1ec44e4a0d04ab67b9
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
small manifests and checked evidence are kept in Git. The completed checkpoints through commit c07c2c9 were merged and pushed to main;
new experiments continue in the isolated research worktree.

## Earlier checkpoint record

The goal is still open: no verified 64-block C(16,5,3) cover has been found. The best unrestricted partial cover still covers557 of560 triples. The best point-essential regular candidate still covers552. No global nonexistence claim follows from these experiments.

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
first-link exclusion union. The reusable inequality in variable heavy patterns is now derived and independently
audited, as recorded below.


## Integrated main and reusable heavy-pattern cut

The research histories were merged at `deeaaca413d5032eb5ec37d1ef8499fae4af93cc`
and pushed to the private repository's `main` branch. Remote and local commit
IDs matched. The merged tree passed 369 tests (three existing SWIG warnings),
`uv sync --frozen`, and Ruff. The receipt is in
`experiments/2026-10-03/main-integration/validation.json`.

The fixed-heavy dual now yields a necessary inequality in all 276 legal heavy
block indicators, in global lexicographic order. The constant numerator is
108773 and the 1200 combined ordinary columns have box maximum 87. Therefore
`sum(c_b h_b) >= 108686`. The old ten-hole tuple has value 98144 and violates
this inequality by 10542, or 5271/500 using the dual denominator 1000.
All six hub graphs remain permitted. This is a conditional regular
four-sevenfold-family cut, not an unrestricted reduction or another whole
first-link exclusion.

The construction checker rejects 15 damaged inputs. A separate root checker
reconstructs all 697 rows directly from point incidences, replays all 531 signed
weights, and rejects six damaged cuts. Its receipt is
`experiments/2026-10-03/lookahead-cut-independent/audit.json`; the coefficient
file and symbolic row map are in `lookahead-parametric-cut/`.

## Joint partial-core pilot

A new model retains all 4368 block variables, selects exactly 64 blocks, and
restricts original-label core overlap to 52 through 55. All 560 hole indicators
are exact in both directions; their sum is minimized. There are no point-degree,
regularity, rotational, or hole-ceiling assumptions. This overlap band is a
construction restriction, not a complete reduction. Root independently rebuilt
all 1122 rows and the objective, checked the entire feasible hint, and rejected
seven damaged models before the run.

The 180-second, one-worker pilot (seed 2026103991) returned FEASIBLE with 11 holes,
exactly its initial hint, and objective lower bound zero. It found no improvement.
Both cover checkers agree on its deficits. A separate containment screen completed
319 group nodes and found no relabeled 60-block core, but the state has five
disjoint heavy triples with counts 6, 7, 6, 6, 7, the previously proved obstructed
profile. It is not a useful escape seed. No global conclusion follows from this
pilot. Artifacts are in `experiments/2026-10-03/partial-core-holes/`.


## Cut-guided native pilot and relabeling screen

The optional native guide adds `ceil(max(0,108686-heavy_sum)/1000)` to the
existing score. It changes no admissible states and keeps unconditional
zero-hole acceptance. The default remains off. The original source is unchanged.
Before the pilot, all 148248 catalog templates were checked in optimized and
sanitizer builds, with 296496 sum comparisons, 130 saved-state checks, 40 forced
operations, and 12 damaged fields rejected. Default-off trajectories matched
the original implementation.

One 300-second native cycle pilot, seed 2026104722, made 81057018 proposals.
Its best has ten holes and score 82, with no unsupported triples, 680 admissible
ordinary blocks, and labeled-cut value 118449. All 45 saved states and 16
operations passed the independent audit and both cover-verifier recounts.
The best witness SHA256 is
`b48c3ce6653c92936ff824fc2d68e29b0ba080c985378c9c85b02418e6849c93`.

Root then enumerated all 31104 template-preserving relabelings of the checked
cut. None excludes this new heavy tuple: minimum value 116376 exceeds threshold
108686. The maximum is 158119. This escapes the entire known cut orbit, but does
not establish that the tuple extends to a cover. A fresh strengthened completion
model is the next diagnostic. The unrestricted best remains three holes.

The orbit check itself received a separate review: independent group closure,
two full-witness relabeling controls, ten malformed/family-invalid controls,
and exact coefficient replay all passed. Its version 1.1 binds hashes to the
exact captured input bytes; the earlier frozen baseline remains valid.

## Steiner quadruple extensions and certified representatives

Fresh primary literature identified 1054163 isomorphism classes of SQS(16):
Kaski, Ostergard and Pottonen, *The Steiner quadruple systems of order 16*,
[DOI 10.1016/j.jcta.2006.03.017](https://doi.org/10.1016/j.jcta.2006.03.017).
The tested construction uses two explicit seeds, not that full classification.
An affine seed and an eight-for-eight parity trade each partition the 560 triples
into 140 quadruples. Their binary ranks are 11 and 12, so they are nonisomorphic.
Each full five-point extension pool has 1680 blocks; their union has 1744.
Selection is unrestricted within this pool, with no block-orbit invariance,
one-extension-per-quadruple, point-degree, or regularity assumption.

Independent reconstruction checked the two triple partitions, every pool member,
all 561 rows of the exact64 model, malformed controls, and positive controls
through both covering verifiers. A 180-second, one-worker pilot (seed 2026104001)
returned UNKNOWN with no witness.

A finite certificate checks 1536 pool automorphisms. The stabilizer of triple
(9,10,11) has order 48, splitting its 30 carriers into six orbits. Every pool
cover has some relabeling containing a chosen representative. Adding their
six-variable OR therefore preserves satisfiability within this pool; it does
not assume the cover is invariant under any permutation. Root independently
replayed all 30 maps and checked that removing exactly this new row restores
the entire original protobuf. Seven damaged models/certificates were rejected.
The reduced 562-row model returned UNKNOWN after its separate 180-second,
one-worker pilot (seed 2026104011), again without a witness. Both saved result
readbacks rejected twelve damaged results. These timeouts are inconclusive.

The next constructive test is a strictly pool-restricted 64-block hole search,
with its greedy initialization and every legal initial exchange independently
audited before a short run. All current checked results are saved in the
`new-construction-web`, `sqs-extension-independent`, `sqs-union-symmetry`, and
`sqs-union-symmetry-pilot` folders. The complete regression suite passed 369 tests
with three existing warnings, and Ruff passed.


## Second checked heavy-tuple obstruction (October 4)

The new ten-hole tuple passes the previous cut orbit, but its own strengthened
completion is now excluded. Root reconstructed all 697 rows over 1200 ordinary
variables and rejected six damaged models before the LP. The new dual has 542
signed rows and denominator 1000. Its weighted lower bound is 12648/1000 while
the ordinary unit box has maximum 108/1000, giving the exact gap 627/50.
Root replayed every coefficient independently and rejected five damaged
certificates. The full six-hub-graph model was used; no CP pilot was needed.

This rules out only this fixed heavy tuple within the regular four-sevenfold
family. It neither excludes a whole first-link representative nor changes the
109-entry registry. A separate membership screen classifies all 24 anchor links
under the six hub graphs. Five graphs hit checked exclusions. The remaining
cycle graph has link IDs cycle-086, cycle-086, cycle-054 and cycle-099; those open
links alone do not imply that their joint heavy tuple has a completion.

The model, registry transports, LP source and dual are in
`cut-pilot-heavy-completion/`. Root's reconstruction and exact dual receipt are
in `cut-pilot-heavy-completion-independent/`. The second parametric cut was
independently replayed. Its threshold is 104444; the source heavy tuple scores
91904, an exact deficit of 12540/1000. The replay reconstructs all 697 incidence
rows and checks 276 heavy and 1200 ordinary columns, preserving all six graphs.

## Complete screen of the saved heavy patterns (October 4)

The earlier native cut-guided pilot saved 45 files containing 32 distinct full
states and 17 distinct heavy tuples. The first two checked cuts exclude five of
these tuples. Testing all 31104 valid relabelings of both cuts excludes the same
five tuples, with no additional exclusions.

The other twelve tuples each have a separately checked rational contradiction
in their full six-hub-graph completion LP. The 24 numerical LP phases took
3.10136 solver seconds in total; exact replay, rather than the solver status,
establishes these conditional exclusions. Their positive gaps range from
11.299 to 20.410. None needed an integer-completion search.

These twelve certificates give twelve further parametric cuts. Together with
the original two, the fourteen-cut bundle excludes every heavy tuple saved by
that pilot. Root independently reconstructed all fourteen models and replayed
the coefficients and exact gaps, rejecting 28 damaged controls. These are
necessary inequalities for the regular four-sevenfold family. They do not
exclude the entire family, add first-link exclusions, or change the global
covering-number bounds. Evidence is in `cut-survivor-lp-screen/` and the
October 4 `cut-bundle-independent/` and `two-cut-orbit-screen/` folders.

## SQS native and focused point repairs (October 4)

The independently audited SQS-union native heuristic stays within the complete
1744-block pool. One 60-second pilot, seed 2026104021, improved the greedy start
from 31 to 23 missing triples. Both cover verifiers independently agreed on
every saved best and final state. This is an incomplete restricted construction,
not an improvement over the unrestricted three-hole partial.

Four focused point-star repairs each ran for 30 seconds with one worker. They
rebuild all blocks containing point 2 or point 15 of the original three-hole
seed, fixing only the retained blocks and allowing all 4368 candidate blocks.
All four runs returned the original three-hole state, with bound zero and no
changed partial. Independent reconstruction checked both complete models and
both cover verifiers agreed on their saved states. The novelty was focused
neighborhood scheduling; broader earlier neighborhoods could already contain
these point-star moves. The timeouts do not exclude either neighborhood.

Fresh primary-source review of Dai's 2006 thesis, Table 7.2, confirms that a
64-block result with cost three was already reported for this instance. Our
three-hole plateau is therefore not a new covering result. The source review
and a separate forced-replacement diversification method are recorded in
`experiments/2026-10-04/local-search-methods/`.

## Forced novelty and direct heavy-pattern learning (October 4)

Six independent ten-second diversification runs forced 8, 16 or 32 incoming
blocks outside the two-seed elite pool, protecting them during that phase and
then releasing all blocks for tabu repair. The saved states contain twelve
distinct three-hole families, including ten new labeled families. All twelve
retain the exact same original 60-block core and the forbidden heavy-triple
profile. All 137 saved-state records passed both covering checks. Labeled
diversity therefore did not escape either obstruction. Evidence is in
`forced-novelty/`; the source review distinguishes this experiment from Dai's
original method and records the altered aspiration and saving behavior.

A smaller master now chooses only the 276 heavy indicators. Its initial 619
rows are the 28-block count, 52 local outside-point equalities, 552 supported
nonanchor triple caps, and fourteen checked cuts. Every proposed pattern is
then tested against the full 697-row ordinary completion LP. A checked signed
dual supplies the next necessary cut when that completion is impossible.
Independent reconstruction matched the complete master and every shifted LP
row; no ordinary integrality or global feasibility claim is inferred.

The first ten cases took 3.122 seconds and produced ten checked cuts. A separate
continuation started with all 24 cuts and checked 100 more cases in 43.194
seconds, reaching its iteration cap. All 100 new certificates and incremental
models passed independent replay. No fractional completion appeared. The mean
exact gap in the first and last ten cases was 21.7122 and 19.7248; these are
descriptive observations, not a convergence guarantee. The resulting 124 cuts
remain restricted to the regular four-sevenfold family. Large models and
certificates stay in ignored scratch, with a compact hash index and source in
`lazy-heavy-master-continuation/`.

## Fourteen-cut native pilot and completion check (October 4)

The native guide uses the largest positive violation among the original
fourteen cuts, rounded up after division by 1000 and multiplied by ten. It
changes only the search score. Legal moves and unconditional zero-hole
acceptance remain intact. Independent preparation checked all 148248 templates,
286 saved states and 88 operations, with optimized and sanitizer builds. A
separate version adds actual terminal-state saving and preserves the earlier
source and receipts.

One 180-second cycle pilot, seed 2026104051, made 53830825 proposals. Its best
state still has ten holes and score 82, but passes all fourteen cuts and has no
unsupported triples. All 54 saved states passed independent score, profile and
cover-verifier recounts. The terminal state has 25 holes. No cover was found.

The new best tuple is nevertheless excluded by a fresh completion certificate.
Root independently reconstructed its model and replayed 568 signed rows: the
weighted lower bound is 16697/1000 and the ordinary box maximum is 159/1000,
giving the positive gap 8269/500. Its numerical elastic objective is
16.68585525272344, worse than the original ten-hole tuple's 10.627554709636422.
Passing the finite cut collection did not imply improved completion fitness.
The next bounded construction test ranks local link switches and measures the
elastic completion objective directly. These results leave the unrestricted
three-hole best, 109 first-link exclusions and the 64-block target unchanged.

## Direct LP-guided link switches (October 4)

A local search now scores a heavy tuple by its ordinary-completion LP's total
row slack. Each move switches two disjoint edges in one anchor link, preserving
the link's outside-point incidences. The generator rejects repeated blocks,
blocks outside the 276-column heavy universe, and excess nonanchor heavy-triple
multiplicity. Independent enumeration reproduced all 132 initial neighbors and
the full 697-row completion model. The ordinary variables retain their original
global lexicographic order.

The bounded pilot evaluated 60 distinct neighbors over three rounds. All LPs
returned numerical OPTIMAL, using 8.515 solver seconds. Its objective improved
from 10.627554709636422 to 9.80113812280173, then to 5.575882992498541. The last
round tested only twenty of 136 neighbors, so it did not establish a local
minimum. Separate readbacks checked all sixty numerical vectors and all 401
candidate row sets generated across the three rounds. Sources, rankings,
budgets, vectors, and the pre-solver preparation failure are preserved in
`experiments/2026-10-04/lp-guided-link-switch/` and its independent audit.

A fresh diagnostic of the selected tuple gave an exact signed-dual gap of
217/40, separately replayed with damaged controls. Its derived heavy-pattern
cut has 276 coefficients and excludes the source tuple by 5425/1000. The
certificate was first checked in the regular degree-20 four-sevenfold model.
The pinned-link argument below now proves those restrictions are necessary
for any 64-block cover retaining these 28 blocks, extending this particular
fixed-pattern exclusion to the full block universe.

Combining those heavy blocks with the original 36 ordinary blocks gives a
distinct five-hole partial. Both cover verifiers reject it as incomplete and
agree on its holes: {4,5,11}, {4,6,11}, {4,8,12}, {4,8,16}, and {8,12,16}.
It has zero unsupported triples and no heavy excess in the restricted score.
This supplies a different repair seed, but does not beat the unrestricted
three-hole baseline. The exact certificate, cut, seed, and profile are saved
in `experiments/2026-10-04/lp-guided-best-lp/`.

A separate complete sweep then evaluated all 136 neighbors of the final
tuple, reusing 23 exact-matching checked OPTIMAL records and solving 113 fresh
LPs. It took 16.921 solver seconds and 18.546 wall seconds. All neighbors
returned numerical OPTIMAL and were worse: the smallest neighbor objective
was 5.644705064246714. This establishes only a numerical stall in the declared
two-edge neighborhood. There was no exact fractional completion or cover.
Primal and dual vectors from every fresh solve are saved. Exact signed weights
derived from those duals give 113 further elastic lower bounds, whose smallest
source gap is 5.644645. Independent exact replay shows their envelope is
positive at every one of the 136 neighbors, with minimum 0.725014. This
excludes their fixed-pattern completions. Only 116 of those lower bounds
exceed the incumbent's exact recounted elastic upper bound, so the remaining
local-optimum comparison still relies on numerical LP results.

## Pinned links force regularity (October 4)

Consider four disjoint anchor triples and four distinct outside hubs. Pin seven
blocks through each anchor, with its own hub appearing twice and every other
outside point once. Every pair in a cover needs at least five blocks. Each
anchor point has two pairs already appearing seven times, so its incident
pair counts sum to at least 79 and its block degree is at least 20.

An anchor point and its own hub occur together in two pinned blocks that both
contain the other two anchor points. Covering all fourteen third points
therefore requires at least sixteen third-point incidences, including these
two forced repetitions. Five blocks supply only fifteen, so each own-hub pair
needs at least six blocks. Each hub has three such pairs; its incident pair
counts sum to at least 78 and its degree is also at least 20. The sixteen
degrees sum to 320 in a 64-block cover, forcing every degree to equal 20.

The saturated pair counts then force all remaining blocks into the 1200-column
ordinary universe and imply every row of the existing 697-row model. The
independent audit reconstructed the pair targets, six hub graphs, triple caps,
and full model; it rejected 25 damaged controls and replayed the exact 217/40
gap. Thus no 64-block completion can retain the selected 28 pins, even when
starting from all 4368 blocks. This is conditional on the stated pin profile,
not a global lower bound. The proof is in
`experiments/2026-10-04/four-seven-pinned-regularity/`.

## Unrestricted repair and nearest-pattern cuts (October 4)

A separate 60-second unrestricted native repair, seed 2026104061, improved the
five-hole seed to three holes in one accepted replacement. Every block slot
could change and all 4368 blocks were eligible. All 1865 traces passed replay;
both covering verifiers checked all four saved states. The final partial has
one degree-19 point, fourteen degree-20 points, and one degree-21 point, but
still contains a relabeled copy of the previously identified 60-block core.
It did not escape the known structural trap or find a cover.

The next heavy master used 238 distinct checked cuts and minimized the number
of blocks replaced relative to the best LP tuple. This was a soft objective,
with no imposed neighborhood radius. One bounded campaign screened 95 heavy
patterns in 177.719 combined solver seconds and 188.375 wall seconds. All
95 received independently replayed exact separating cuts, bringing this
collection to 333. The best newly tested elastic objective was
5.966796868079938, so the incumbent remained 5.575882992498541. All 95 shifted
models, incremental masters, primal vectors, and exact cuts passed separate
replay. Master FEASIBLE statuses do not prove nearest-pattern optimality.

Larger finite move enumeration found 660 legal proper three-edge switches in
one anchor and 6900 legal paired two-edge switches across two anchors. The
113 sweep cuts initially excluded all but 27 of these candidates. The final
333-cut envelope excludes all remaining 27 as well. This closes only those
declared neighborhoods. The next distinct experiment will prefer patterns
furthest inside the known necessary inequalities, then measure their actual
completion LP, without assuming that a better surrogate gives a cover.

## Maximum-margin pilot and prior-exclusion check (October 4)

One separate 20-candidate pilot maximized the minimum normalized slack in the
333 known heavy-pattern inequalities. Its 277-variable master retained the
same heavy family, with one nonnegative margin variable and no distance
objective. All twenty masters returned FEASIBLE, so no optimal-margin claim
is made. All completion LPs returned numerical OPTIMAL and yielded separately
checked positive exact cuts. The collection reached 353 cuts. The run used
62.476 combined solver seconds and 65.540 wall seconds; its best new elastic
objective, 18.723394713737736, was worse than the previous patterns. A larger
margin inside finitely many inequalities did not improve actual LP fitness.

A subsequent registry audit found a missed search-efficiency constraint: the
new heavy master and two-edge generator did not enforce the already checked
109 first-link exclusions. The numerical 5.575883 pattern is already excluded
under all six hub graphs. Its fourth seven-block anchor link alone blocks all
six, giving a shorter family-conditional seven-block nogood. This does not
invalidate the saved LP certificates, but the pattern is not an eligible
starting point for further construction search. All historical run records
remain unchanged.

Nearest-master step 038, with broad objective 5.966796868079938, has one
registry-open hub graph: excess vector [0,1,1,1,1,0] in lexicographic hub-pair
order. Its four links map to cycle-061, cycle-061, cycle-086, and cycle-086.
Two independent transport replays checked the archived orbits, point maps,
and proof-registry membership. Subsequent local search must filter all four
links before solving and bind its cache to the six exact hub-pair targets;
the old broad LP score is not a fixed-graph score. Evidence is in
`lp-guided-first-link-registry/` and its independent audit.

A fresh one-worker LP fixed that graph's six hub-pair counts to
[5,6,6,6,6,5]. It returned numerical objective 8.024244815488677 in 0.140
solver seconds. Independent reconstruction of all 697 rows and 1200 columns,
followed by exact dual replay, gives a positive gap of 8024127/1000000.
This particular tuple cannot complete, but its graph remains an eligible
branch for changing the heavy blocks. The branch fitness baseline is 8.024,
not the broader 5.967 score. No integer search was needed for this diagnostic.

The same frozen registry checker also screened all 95 nearest-master and 20
maximum-margin tuples without optimization. Of 115 distinct labeled tuples,
51 retain at least one hub graph and 64 are already excluded under all six.
The five lowest broad scores among survivors all retain graph 1 only.
These are candidate starting points, not fractional or integer completions;
their fixed-graph objectives have not all been evaluated.

The newer public Covering Repository was also accessible on October 4.
Its visible V=16, K=5, T=3, M=3 result still lists 65 blocks, lower bound 61,
and Rade Belic's 1997 entry imported from Dan Gordon's repository. This
agrees with the pinned primary archive. The read-only browser observation is
saved in `coveringrepository-refresh/`; it is not evidence that no unlisted
later result exists.

## Registry-filtered fixed-graph descent (October 4)

The independently gated graph-1 descent started from nearest-master step 038
with its correct fixed-graph elastic objective, 8.024244815488677. It completed
two full two-edge-switch neighborhoods. Each had 136 distinct candidates;
the proof registry rejected 14 before any LP call and admitted 122. Across
both rounds, 243 fresh LPs and one cached baseline all returned numerical
OPTIMAL. The one accepted move improved the objective to 7.52051548546158.
The second round's best neighbor was 7.978655120128314, so descent stopped.
The run used 31.963778 solver seconds and 35.753818 wall seconds.

Independent replay rebuilt both neighborhoods, all registry transports, all
170,068 shifted rows, the cache identity, and all primal and dual hashes.
This establishes a numerical local minimum only in that registry-filtered
fixed-graph two-switch neighborhood. The improved 28-block heavy pattern,
stitched with the original 36 ordinary blocks, misses 17 triples according
to both cover verifiers. No fractional completion or 64-block cover was found.
Sources and receipts are in `g1-link-descent/` and
`g1-link-descent-independent/`; graph-specific results remain separate from
the 353 broad heavy-pattern cuts.

Two older matching-family seeds also survive the full first-link registry.
The native soft-search raw-best seed misses 17 triples and has graph-5 classes
matching-057, matching-064, matching-043, matching-013. Its score-best sibling
misses 19 and replaces the fourth class with matching-069. Their intended
graph-5 hub-pair targets are [7,5,5,5,5,7]; the partial seeds do not already
satisfy every target. A separate independent gate reconstructed both models,
all eight registry maps, and all shifted rows before two one-second LP calls.

Both calls returned numerical OPTIMAL, using 0.262139 solver seconds in total.
Their elastic objectives were 15.06922063054413 and 15.317006713016973.
Separate exact dual checks produced positive gaps 15069111/1000000 and
3063381/200000. Thus neither fixed heavy tuple can complete in its specified
matching graph. Independent postchecks recounted all ordinary variables,
slacks, rows and signed-dual arithmetic. These are useful alternate search
baselines, not fractional or integer completions. The saved work is in
`matching-seed-registry/`, `matching-g5-lp/`, and
`matching-g5-lp-independent/`.

The graph-1 descent's best tuple also has a separately replayed exact gap,
940057/125000, from 517 signed row weights. Its exact primal elastic upper
bound is 7.520515486. This excludes that fixed tuple, without excluding
other graph-1 heavy patterns.

The new checkpoint's package regression passed all 369 tests in 244.67
seconds, with the same three SWIG warnings. `uv sync --frozen`, Ruff and
whitespace checks also passed. The regression receipt and log hash are in
`registry-matching-validation/regression.json`.

## Larger fixed-graph moves and a matching descent (October 4)

At the graph-1 local minimum, independent enumeration found 580 registry-safe
proper three-edge changes, 5,541 safe paired two-anchor changes, and 100,076
safe whole-link replacements. The 243 graph-specific dual planes from the
descent, together with 353 broad planes, give positive exact bounds for every
three-edge and paired change and for 99,319 whole-link replacements. These
are exclusions of declared finite neighborhoods. Positive bounds alone do
not say that all their elastic objectives are worse than the incumbent.

The remaining 757 whole-link replacements were all uncached. Their frozen
LP sweep passed an independent gate covering all 527,629 shifted rows and
3,028 link classifications. All 757 calls returned numerical OPTIMAL; none
gave numerical zero or improved the incumbent. The best new objective was
10.613462674257228. The sweep used 101.289012 solver seconds and 110.185592
wall seconds. A separate postcheck replayed every model, vector and dual.
All 757 new signed-dual certificates subsequently passed independent exact
replay, along with the previous 243 graph-specific planes. Their minimum
new gap is 165832/15625. The exact prior 99,319 exclusions plus these 757
close all 100,076 declared registry-safe whole-link replacements. This does
not exclude the whole graph-1 family or prove an elastic local optimum.
Unchanged generator sources and compact restorable certificate archives are
tracked in `g1-larger-source/` and `g1-whole-link-certificates/`.

The matching graph-5 descent completed three full neighborhoods, admitting
86, 86 and 84 states after registry filtering. It used 253 fresh LPs and
three cached values, improving 15.06922063054413 to 13.221637797152143,
then 12.594498845064832 and 11.500690015970484. All LP objectives remained
positive. Independent reconstruction checked the neighborhoods, all shifted
rows, registry mappings and cache history. The run used 33.945800 solver
seconds and 38.150497 wall seconds. It stopped at its three-round limit;
the last accepted pattern has not yet been shown to be a local minimum.

Stitching those three improved heavy patterns with the original 36 ordinary
blocks produced partial states with 18, 20 and 21 missing triples. Both
cover verifiers agree. The lower LP score therefore did not improve the
integer coverage of these particular stitched states. Their provenance is
kept separately in `g5-link-descent-stitched/`.

## Heterogeneous block recombination (October 4)

A different construction pilot recombined blocks from ten separately checked
partial covers, spanning unrestricted, regular, SQS, native and fixed-graph
searches. Their union contains 277 blocks; a second pool adds 60 reproducible
random blocks from outside that union. Every triple has at least two carriers
in each pool. Independent reconstruction checked all 4,928 variables, 1,122
rows, complete hints, seed profiles and random additions, and rejected 19
damaged controls. The models impose only pool membership, cardinality 64 and
560 exact missing-triple indicators, with no inherited family constraints.

Both 30-second, four-worker runs returned FEASIBLE with three holes. Their
callbacks kept the original hint. Independently extracted final responses
contained different equal-score states, each verified by both cover checkers.
Those final states have degree histogram 19:2, 20:12, 21:2 and retain the
original forbidden 60-block core. Their separating histograms differ from
all ten inputs, but they do not improve coverage or escape that core.
The independent postcheck distinguishes callback incumbents from final
equal-score solver assignments. No pool-optimality or global exclusion
follows from these bounded runs.

A separate pair of pool runs added two explicit 60-block core-avoidance rows.
Their exact model and five-hole hint passed an independent delta gate.
Both 30-second runs returned FEASIBLE with five holes. Callback states and
independently extracted final ties passed both cover checkers. The final
states retain 59 blocks of one core and still trigger the broader proved
five-heavy obstruction: five disjoint triples have multiplicity at least
six, with at least two sevenfold. Core avoidance alone therefore did not
escape that obstruction. Among the ten input seeds, the SQS state and the
two matching states avoid both tested partition obstructions; the best of
those inputs has 17 holes. These checks concern the two specified partitions.

## Matching continuation and a larger cycle master (October 4)

The independently gated graph-5 continuation improved its elastic objective
through 9.533204639679104, 9.448398722490406, 8.818415543401665 and
8.152937802508724. Five complete neighborhoods used 465 fresh LPs and 14
cached values. The last neighborhood admitted 105 states; its independently
recounted minimum was 8.279923931332881, so the run stopped at a numerical
two-switch local minimum. Independent replay checked all neighborhoods,
registry mappings, shifted rows, vectors and cache entries. Total cost was
61.726966 solver seconds and 68.664317 wall seconds. No fractional completion
or integer cover was found.

The larger graph-1 master combines 353 broad cuts, 1,000 graph-specific cuts
and 19 checked seven-block registry nogoods with the original heavy-family
rows. Its 276-variable, 1,977-row model retains a soft distance objective with
no radius. Independent reconstruction passed. Its first two-second call
returned UNKNOWN after spending its budget in presolve, with no search
branches, candidate tuple or LP call. This is inconclusive. Separate bounded
presolve-on/off diagnostics use the identical model and are recorded separately.


## Profile-filtered recombination and checked matching neighborhoods (October 4)

The two profile-filtered heterogeneous pool searches each used 60 seconds and four workers. Both returned FEASIBLE and improved the eligible 17-hole matching hint to six holes. These do not improve the unrestricted three-hole best. An independent outcome checker reconstructed every value and checked every active row in all 22 callback/final states. All 44 covering-verifier calls agreed; six damaged assignments were rejected. No checked state contains any five disjoint triples of multiplicity at least six with two at least seven. The final solver ties differ from the best callbacks and are saved separately. Every best-six state still retains 59 blocks of the original core; passing the obstruction scan does not establish extendability.

A separate finite enumeration examined all 275,456 one-block replacements of each of four checked best-six states. The 49 raw improving exchanges all restore a forbidden five-heavy pattern; no profile-eligible single exchange improves the hole count. This motivates a multiblock release, not a new global obstruction. The union of these four states has 72 blocks, their 12 distinct holes have 720 carriers, and adding all those carriers to the earlier elite pool yields a 952-block construction pool. See `six-hole-next-route/` for source, hashes and scope.

The fixed-g5 larger screen independently replayed 720 exact conditional planes, separate from 353 broad planes. All 492 declared proper-three-edge states and all 4,106 paired-anchor states have positive bounds; minimum exact bounds are 1.910640 and 2.578784. Among 46,436 registry-safe whole-link replacements, 42,940 are excluded and 3,496 remain unexcluded and uncached. The compact archive reconstructs the exact 42,202,869-byte full bundle, which remains in ignored scratch. This is a finite-neighborhood result under graph 5, not an exclusion of the full matching branch. Evidence is in `g5-larger-screen/` and `g5-larger-independent/`.

The graph-1 presolve diagnostic showed that disabling presolve produces proposals within the intended short master budget. Its independently checked continuation made 42 proposals (41 OPTIMAL, one FEASIBLE), all at replacement distance six. Sixteen were rejected by the full four-link registry; 26 admitted completion LPs were OPTIMAL. None improved 7.52051548546158; the best fresh value was 9.141496147218286. It used 115.1513965812 combined solver seconds and 130.7668848750 wall seconds within frozen 120/160-second limits. The independent checker rebuilt every master, checked assignments and traces, replayed all 1,027 g1 planes and 38 final nogoods, and rejected seven damaged controls. No numerical zero, fractional completion or integer cover was found. Evidence is in `g1-master-presolve-diagnostic/`, `g1-nearest-master-continuation/` and their independent sibling folders.


## Exact matching-neighborhood closure and stronger core corrections (October 4)

The fixed-g5 whole-link sweep evaluated 3,441 of 3,496 survivors before its wall guard: all numerical OPTIMAL, no improvement over 8.152937802508724. It used 497.4939717227 solver seconds and 625.1666496660 wall seconds. Independent numerical readback reconstructed every saved model, vector and registry receipt. Exact signed-row extraction then produced 3,441 new positive certificates; their minimum gap is 8471339/1000000. The new planes also exclude all 55 unexamined states, with minimum tail envelope 6980899/1000000. Root's independent replay checks every new plane, every tail envelope, the complete finite union and exact archive restoration. Together with 42,940 prior exclusions, all 46,436 declared registry-safe whole-link replacements are excluded under graph 5. The 4,161 graph-specific planes remain separate from the 353 broad planes. This closes that finite neighborhood only; it does not exclude the matching family or prove a global bound. See `g5-whole-link-pool/`, `g5-whole-link-certificates/`, `g5-whole-link-tail-screen/` and independent sibling folders. Large proof archives remain outside Git.

Two 120-second release pilots, using the 952-block expanded hole-carrier pool and full 4,368-block universe, both retained six holes and original-core overlap 59. All four callback/final records (three distinct families) passed paired covering checks, complete row readback and global five-heavy scans. These results nevertheless fail a stronger previously saved core restriction. Fresh standalone replay of `core-remove-4.json.gz` checks 8,337 representatives covering all 487,635 four-removal sets and proves that any 64-block cover retains at most 55 of the 60 core blocks. The minimum residual-cover lower bound is 2035711/250000, strictly greater than the eight available additions. Both named core label maps were independently checked across all 4,368 blocks and 43,680 incidences. The old <=59 rows were weaker than available evidence. No <=54 bound follows from the partial five-removal results. Evidence is in `core-cap-independent/`.

The corrected <=55 pilots started from a checked 14-hole hint and used the same two pools and 120-second/four-worker budgets. The adaptive pool reached 13 holes; the full pool reached three. Independent postcheck verified all 15 saved/final records, with 14 distinct families. Eight full-pool records, including the final three-hole result, violate a newly labeled five-heavy partition: (1,2,3), (5,6,7), (8,12,16), (9,10,11), (13,14,15). Thus the apparent three-hole result is not a qualified escape. A finite 933,120-map enumeration found that it contains all 60 blocks of another relabeled original core. A separate full-incidence map check proves the third <=55 row. The explicit map is enough to justify that row; no exhaustive claim over all16! label maps is made. See `six-hole-strong-core-release/`, its independent folder, `six-hole-relabeled-core-transport/` and `third-core-independent/`.

A new necessary relabel screen is also checked: if any image of the original core overlaps a family in at least 56 blocks, some five disjoint triples must satisfy sum(max(0,6-count))<=4. Each of the five core triples has multiplicity six, and a removed five-block can contain at most one of these disjoint triples. Absence of such a partition excludes every >55 core image; presence is inconclusive. The saved strong-pilot states all have a candidate partition, so this screen alone does not certify their full core-image eligibility.

A fresh live repository-table check on 2026-10-04 at 10:29:52 UTC still shows lower bound 61 and upper bound 65 for the exact target. A separate read-only primary-source review records Knuth's SSMCC interval-cover encoding and failure-weighted variant as an unrun alternative. It is not a new algorithm or a demonstrated performance gain. Sources and generator notes are in `next-route-source-review/` and `ssmcc-model-plan/`.

The current checkpoint passed `uv sync --frozen`, all 369 tests (235.28 seconds, three existing SWIG warnings), and Ruff. The regression log hash is saved in `profile-core-validation/regression.json`. No package source changed during these experimental pilots. No verified 64-block cover has been found.


## Three-core releases and a global five-heavy filter (October 4)

The next two releases retained all three checked core caps and all three named profile filters. Pools stayed at 952 and 4,368 blocks, but used different legal hints (13 and ten holes), so they are not a controlled pool-size comparison. Both 120-second/four-worker calls returned FEASIBLE: the adaptive pool improved to twelve holes, and the full universe retained ten. Independent checks covered five callback/final records (four distinct families), all assignments, both covering verifiers and every global five-heavy obstruction. None had that obstruction. Final core overlaps were [1,7,50] and [1,7,55]. Both finals have minimum point degree 19 and minimum pair count 4. The former has five pairs below five, the latter three. The elementary necessary pair bound follows because each pair belongs to fourteen triples and each selected block through it supplies at most three; summing the fifteen pair counts at a point gives its degree bound of nineteen. These pair diagnostics did not change either model.

A new exact global encoding removes the need to enumerate named five-heavy partitions. Each triple receives exact threshold indicators for multiplicities at least six and at least seven and weight 5*six+seven in {0,5,6}. A canonical minimum-point recurrence lower-bounds the maximum weight of every partition of a point subset into triples. Bounding every fifteen-point target by 26 excludes exactly the forbidden five-disjoint-heavy pattern. The least feasible DP values equal the maxima; other feasible DP assignments can have slack. The existing unrestricted theorem therefore justifies the encoding for any full 64-block cover.

The full recurrence has 21,845 states and 502,516 rows. Keeping only states reachable downward from the sixteen fifteen-point targets preserves every relevant partition and gives 4,410 states and 99,917 rows. Independent proof reconstruction matches the saved graph bytes, verifies both reachability directions, all 4,410 constructive paths, 79 threshold counts, 243 category patterns, 2,028 direct small cases and six full/trimmed comparisons. It also replays the existing theorem's 27,040 degree/hub assignments. Root separately checked the serialized 10,488-variable, 103,345-row model and complete ten-hole hint, retaining the previous three-core/named-filter prefix and objective unchanged.

The sole declared global-DP pilot used 120 seconds, four workers and seed 2026104104. It reached search after about two seconds and returned FEASIBLE with the original objective 651 and ten-hole block family. All saved callback and final values, domains, active rows, exact thresholds and actual partition maxima were independently checked, including four covering-verifier calls and three damaged-assignment controls. There was no improvement or covering witness. Sources, proof controls, exact gate and outcome are in `global-five-heavy-dp-plan/`, `global-five-heavy-dp/` and `global-five-heavy-dp-independent/`. This is an encoding/result checkpoint, not a nonexistence theorem or a new global covering bound.

## Core-cap escape and necessary pair-link cuts (October 4)

The isolated native core-cap search keeps all 64 slots mutable and all 4,368 blocks eligible. It hard-rejects moves exceeding any of the three checked core caps, uses the prior global five-heavy traversal penalty, and records only profile-qualified best states. An independent preflight found missing final counters on zero-hole exits before any optimization. The unrun first revision is preserved; a second frozen revision emits and checks final best/current status on every exit. Independent sanitizer controls exercised 210 joint boundary cases, including 25 rejections, 92 commits and 93 rollbacks, all 13,104 core membership bits and malformed inputs.

Exactly two sixty-second native runs used seeds 2026104201 and 2026104202. The first improved ten holes to nine after 318,360,448 proposals; the second retained ten after 297,376,832. They rejected 37 and 36 over-cap moves respectively. All seven saved/final records (four distinct families) were independently recounted and passed paired covering checks for their stated hole counts. Final-current diagnostics have 56 and 66 holes and are separate from best records. The new nine-hole family has no five-triple partition satisfying the necessary core-image deficit test, so it retains at most 55 blocks of every relabeling of the old core. It still has four pairs below five. This is a qualified escape from that core trap, not a covering witness. See `native-core-cap-escape-v2/` and `native-core-cap-escape-independent/`.

A bounded inventory checked 202 paths representing 134 distinct families, with 17 distinct families passing the pair minimum, global profile filter and three named core caps. The best has six holes, all point degrees twenty, pair minimum five, global partition weight 22 and core overlaps [2,2,0]. Its exact historical source, runner, binary and inputs were recovered by recorded hashes. A sibling DP model adds exactly 120 pair-minimum-five rows to the unchanged 103,345-row parent, replaces its complete hint with this family, and retains all 4,368 block variables. The independent gate checks every carrier set and hint value, plus damaged-row controls. Its sole 120-second, four-worker run, seed 2026104105, retained six holes while reducing original-core overlap from two to one (objective 392 to 391). All three callback/final records, every active row, all actual global partition maxima and both covering verifiers were independently checked. See `pair-five-hint-inventory/`, `global-five-heavy-pair-five/` and its independent folder.

Stronger local inequalities explain a remaining defect in these seeds. Write c(S) for the number of selected blocks containing S. For any pair P contained in a triple T, every cover satisfies 3*c(P)-c(T)>=13: the left side is exactly the sum of the other thirteen triple counts through P. For a quadruple Q containing P, every cover satisfies 3*c(P)-2*c(Q)>=12: its left side contains the twelve other triple counts and two nonnegative differences. These bounds need no equal-degree assumption. Their earlier local derivations were present in the regular-heavy report; only that report's later hub conclusions required regularity. Independent reconstruction checked 4,586,400 carrier-column identities, the complete 65-block benchmark and four damaged controls. The six-hole hint violates four pair-triple rows by one each, with c(P)=c(T)=6, and no pair-quadruple rows. None of the seventeen eligible inventory families passes both cut families. The nine-hole native family violates 56 triple rows and 48 quadruple rows. Proofs and direct-count diagnostics are in `pair-local-necessary-cuts-independent/` and `pair-five-hint-inventory/PAIR-LINK-DIAGNOSTICS.md`.

The next isolated preparation uses explicit pair, triple and quadruple counts to impose these necessary inequalities in a smaller model. The six-hole block guidance is explicitly infeasible for those stronger rows and will not be described as a legal complete hint. No new global covering bound or nonexistence conclusion follows from the completed runs.

## Stronger compact cuts, a fourth core, and pair-penalty results (October 4)

For pair P and two different outside points a,b, the stronger inequality 3*c(P)-c(Pa)-c(Pb)>=12 is the exact sum of the other twelve triple counts through P. It dominates the earlier quadruple row because both c(Pa) and c(Pb) are at least c(Pab). Independent checks cover all 3,974,880 carrier-column identities and dominance comparisons. If c(P)=5, the two largest distinct-position counts sum to at most three, while all fourteen counts total fifteen; the only possible sorted vector is (2,1,...,1), so every triple through that pair is covered. All 175 sorted nonnegative fourteen-count vectors totaling fifteen were checked. Tied count values must retain their distinct positions. Evidence is in `pair-two-necessary-cuts-independent/`.

A separate proof shows the pair floor and earlier single/quadruple cuts already imply the global five-heavy exclusion, even for incomplete 64-block families. Five disjoint heavy triples force fifteen point degrees to be at least twenty and the remaining degree to be at least nineteen, totaling 319. Each sevenfold triple supplies a repeated outside hub. The pair cuts force every two hub roles to raise that minimum total to at least 321, exceeding the available 320. An independent finite audit checks all 1,690 role choices and 69,888 point-pair identities. The stronger two-triple cuts inherit this implication by dominance. Actual output profiles are still recounted separately. See `pair-cuts-imply-profile-independent/`.

The weaker explicit-count model was frozen and independently checked at 7,428 variables and 16,224 rows, but remained unrun when superseded by the stronger sibling. The stronger model has 5,608 variables and 14,404 rows, exact pair/triple counts and hole flags, all 4,368 block choices, three core caps, 1,680 single-triple rows and 10,920 two-triple rows. There are no fixed point degrees, symmetry assumptions or DP states. The six-hole guidance specifies only block values; its unique count extension violates four single rows and 62 stronger rows. Its sole 120-second/four-worker run with seed 2026104301 returned UNKNOWN after 120.011303 solver seconds, with no callback or feasible final assignment. Native search began at 0.96 seconds, so setup was not the bottleneck. Independent native-response and log checks confirm exactly one call, no witness and no infeasibility conclusion. Folders are `compact-pair-local-counts/`, `pair-local-counts-independent/`, `compact-pair-two-counts/` and `pair-two-counts-independent/`.

The six-hole guidance also falls into another old-core trap. Its unique necessary heavy partition allows 933,120 core maps; both producer and independent C++ enumeration find maximum overlap 59 with 60 maximizing maps. An explicit map and inverse were checked across all 4,368 blocks, 560 triples and 43,680 incidences, transporting the previously proved cap of 55. The necessary-partition filter makes this maximum global over all relabelings for this candidate. This supplies a fourth safe core cap; the already frozen runs still contain only the original three. The original transport source is preserved unchanged, with one local historical E501 lint exception; the active v2 source fixes that long literal. See `recovered-six-hole-core-transport-v2/` and `fourth-core-independent/`.

An isolated native pilot used soft energy 20*holes + 5*D3 + D4 + 160*forbidden-profile, where D3 and D4 sum the earlier single-triple and quadruple deficits. All slots and blocks remain available, with the three named core caps hard. Independent sanitizer controls check 901 direct recounts, 360 commits, 337 rollbacks and all five block-intersection sizes. Exactly two sixty-second runs, seeds 2026104401/2026104402, made 37,532,768 and 38,683,744 proposals. Neither improved the six-hole raw/soft-score best. Separate zero-D3/D4 records reached 48 and 49 holes, both with pair minimum five and point degrees from nineteen to twenty-one. Independent postcheck covers all 21 records/twelve distinct families and 24 fresh covering-verifier calls. Both finals have no necessary core-image partition, proving overlap at most 55 under every relabeling of the old core. Their 242 explicitly tested images have maximum overlap five; that finite screen is not the basis of the all-relabel statement. See `native-pair-penalty/` and its independent folder.

These two partials fail the stronger two-triple rows. Their maximum-per-pair deficit sums are 75 and 74 (full row-deficit sums 175 and 170), versus 14 (full sum 62) for the six-hole seed. They are useful evidence of escaping the old core while meeting weaker pair rules, not feasible hints for the stronger model. Next preparation targets a family with zero stronger deficits and all four checked core caps before another compact solver call. No verified 64-block cover has been found.


## Direct stronger-deficit pilots and a soft-model result (October 4)

The new native pilot uses the exact sum of maximum two-triple deficits per pair, with a separate raw-hole record and four hard core caps. Both declared 60-second seeds exhausted their budgets. Seed 2026104501 reached deficit 46 with 33 holes (full row-deficit sum 267); seed 2026104502 reached deficit 56 with 59 holes (full row sum 510). Neither found zero deficit. The second run separately saved a raw 47-hole family satisfying the weaker pair rules, but its stronger deficit is 75. The compact deficit can fall while the full row-deficit sum rises; neither score is a covering witness. Independent recounts and both verifiers checked all 115 unique saved families, requiring 230 verifier calls. Sources, frozen hashes and results are in `native-pair-two-penalty/` and `native-d2-independent/`.

The soft CP model retains exact pair/triple counts, exact hole flags, pair floors, the single-triple inequalities and all four core caps. Its 120 new nonnegative deficit variables soften exactly 10,920 stronger rows; the objective is 561 times the deficit sum plus the holes. The complete 49-hole guidance has deficit 74 and objective 41,563 and passes every soft-model row. The independent model gate ignores variable names only, compares all other original proto fields exactly, checks each changed row and new variable domain, and binds the complete hint, source, proof and parameter hashes. Decreased required-deficit controls fail and valid auxiliary slack is accepted.

The sole 120-second, four-worker CP call (seed 2026104302) returned FEASIBLE without improvement. Its one callback and final vector both retain the same 49-hole family, deficit 74, full row sum 170 and objective 41,563; the objective bound is zero. Independent replay checked both complete 5,728-value assignments and all 14,405 rows, plus the two covering verifiers. There is no zero-deficit hint, 64-block cover, or infeasibility result. See `soft-strong-pair-four-core/`, `soft-pair-two-independent/` and `soft-pair-two-postcheck/`.

A separately checked hard extended formulation uses the proved top-two identity with 120 threshold variables and 1,680 positive-part auxiliaries. Its 7,408 variables and 3,605 rows retain the exact necessary pair condition and four checked core caps, with holes as the only objective. The single 120-second, four-worker run (seed 2026104601) returned UNKNOWN without callbacks or a feasible vector. The independent runtime audit verified the empty native solution, all hashes and the final status. This is an equivalent representation, but no search benefit has been measured and no infeasibility claim follows. See `hard-top-two-extended-four-core/` and `hard-top-two-independent/`.

The completed checkpoint passed frozen dependency sync, all 369 tests (258.05 seconds), full Ruff and diff checks. The three existing SWIG deprecation warnings remain. The validation record is in `stronger-pair-checkpoint-validation/`.


## Published add/drop method and the next construction pilot (October 4)

A new primary-source review found the authors' implementation of NuSC (Luo, Xing, Cai and Hu; DOI 10.1109/TCYB.2022.3199147). The selected mechanism is a variable-cardinality two-drop/add-repair walk with dynamic weights, a redundancy score and configuration checking. At incumbent size 65 it may walk through 64, 62 and 63 selected blocks; it does not inherently make 65/66 excursions. The existing native search already has hole-driven weighted 78-carrier exchanges, so that part alone is not new. The author source has no forgetting/decay rule. Its source revision, exact algorithm references, GPLv3 license, retrieval limitations and other inspected primary leads are saved in `post-d2-literature/`. No upstream GPL code is copied into the tracked implementation.

The independent implementation completed its two declared 120-second seeds from the verified Belic 65-block cover. Both exhausted their budgets without a complete family of size at most 64. They took approximately 17.0 million and 15.9 million iterations; the live family sizes ranged from 62 to 65. The best complete family stayed at 65 blocks. Both raw exact-64 records stayed at the initial three-hole family retaining all 60 blocks of the forbidden old core. The separate four-named-core-cap-admissible records reached 13 and 12 holes. Core caps only classify exact-64 records; they are not extrapolated to other sizes or imposed on intermediate trajectories. The independent postcheck inspected all 19 saved/final states (11 distinct families), both verifiers, the first 32 transitions per seed, raw logs, frozen hashes and the sequential/first-cover stop policy. Sources and results are in `native-variable-cardinality/` and its independent sibling.


The best new admissible family, H12 (seed 2026104702, SHA256 `330788e4a6f24e1852b047f5cd2447bfa83da66ea8c6daba3287eb53088c4b00`), has no necessary old-core partition. A separate complete necessary-condition screen therefore proves its overlap is at most 55 for every relabeling of that old core. It still fails both covering tests with 12 missing triples; passing this screen proves no covering bound. See `native-variable-cardinality-relabel-screen/`.

Independent structural profiles distinguish H12 from the earlier all-relabel-core-free H9. H12 has point counts {19:5,20:6,21:5}, pair counts {5:83,6:34,7:3}, and satisfies every weaker single-triple and quad inequality. Its stronger deficit is 34 under both maximum-per-pair and full-row summation. H9 has point counts {19:5,20:7,21:3,22:1}, four pairs occurring only four times, and stronger deficit sums 23 and 639 respectively. Both remain noncovers. H12 improves the hole count of the available weaker-pair-qualified hints from 48/49 to 12; H9 remains the better raw-hole starting family outside every old-core relabeling. Exact counts and receipts are in `native-partial-start-profiles/`.

The next preparations use those two different partial families as live native starting states while retaining Belic65 as a separate verified complete incumbent. A parallel soft-model preparation uses H12 as a complete feasible hint of objective 19,086 for the unchanged soft-pair model. These are search preparations, not completed optimizer results. No verified 64-block cover has been found.


## Longer partial starts and a stronger H12 hint (October 4)

The 300-second soft-pair call from H12 (four workers, seed 2026104901) returned FEASIBLE with three callbacks and a final vector. Independent replay checked all four complete 5,728-value vectors and every row; two distinct families were checked by both covering verifiers. Actual maximum-per-pair and full-row deficits improved from 34 to 32 while all 12 uncovered triples remained exactly unchanged. The change replaces block {4,5,7,10,15} with {5,7,10,12,15}; the other 63 blocks remain. Callback2 has one unit of valid auxiliary slack (solver deficit33 versus actual32); callback3 and the final vector use32. The final canonical objective is 17,964, the bound remains 0, and no actual-zero stronger-deficit hint was found. This is a surrogate improvement, not a reduction in missing triples. Sources, the independent gate, runtime checks, and relabel/novelty receipts are in the `soft-pair-h12-*` folders. A tracked exact-byte copy of the improved H12 family has SHA256 `cadb86e4f2243eada269dc314bca0bc5c238f5b0ca2bd9525dd0b67aad24c970`; it again has no necessary old-core partition, certifying every relabeled old-core overlap is at most 55.

The separate partial-start native campaign completed exactly two sequential 300-second calls, retaining the verified Belic65 complete incumbent separately from the live64 partial. Seed 2026104801 kept its initial H9 after 39,293,091 iterations and ended 64/H18. Seed 2026104802 improved H12 to H10 after 42,912,188 iterations and ended 62/H32. Both live size ranges were 62 through 64, both had exactly four initial age-filter fallbacks, and neither found a cover. The independent postcheck verified all 18 saved/final paths (seven distinct families), zero-mutation starting records, the first 32 moves of each run, family metrics, both cover verifiers, frozen log hashes, and sequential/first-success stopping. These timings overlapped the soft CP run and are not a controlled speed comparison. See `native-variable-partial-start/` and its independent sibling. The new H10 has pair minimum 4 and fails the weaker pair inequalities, so it cannot replace H12 as a feasible hint for the current soft model.

The next preparations target actual holes directly. A soft-model sibling retains every row/domain/core cap, but uses 15361 times the holes plus the deficit sum ; 120 auxiliaries bounded by 128 make 15361 strictly dominate every possible deficit difference. It stops only on an actual dual-verified cover. A separate finite scan will inspect the 275,456 one-block replacements of the improved H12 family and retain neighbors meeting the weaker necessary rules and four named core caps. Its conclusions will apply only to that local neighborhood. These preparations have not yet produced an optimizer result. No verified 64-block cover has been found.


## Hole-priority result and complete one-block neighborhood (October 4)

The frozen hole-priority CP call (seed 2026105001, four workers, 300 seconds) returned FEASIBLE after 300.01341 solver seconds. Independent replay checked both callbacks and the final 5,728-value vector against every domain and all 14,405 rows. Both distinct families passed the two parsers and were correctly rejected as covers. All 12 holes stayed unchanged; the actual per-pair and expanded stronger-row deficit sums improved from32 to31. The final objective is184363 with bound0. No actual-zero-deficit partial or full cover appeared. The independent postcheck is `soft-pair-hole-priority-postcheck/postcheck.json`, SHA256 `7d75f7a3e30bd8587727c6b6f90ff8702e15b1e092914866246bf647d699e9be`. Its positive-slack and damaged-vector controls passed.

The separate frozen one-block scan used the earlier H12/D32 family, never the newer D31 family. Its sole native pass completed all275456 distinct replacements in0.521694 seconds;8667 met the pair-floor, single, quadruple and four named core restrictions. None reduced the12 holes. There were22 strictly improving neighbors by the declared lexicographic hole/deficit rank, three successive records, and four final best ties atH12/D29. The producer reconstructed and dual-checked every saved distinct family. The independent runtime audit checked the frozen loop structure, fixed axes, normal exit, terminal count and unique swap ordinals, then directly recounted and dual-verified all six saved distinct families, including all four best ties. It did not repeat the full enumeration or independently recalculate every unrecorded metric. Its receipt is `weak-pair-swap-scan-runtime-independent/postcheck.json`, SHA256 `a491a5ae273d2eab20bff3c3992771ce130d3293236eee62d9c05c6214e1207c`. This finite result is only about one-block replacements from that exact pinned family under the listed necessary rows. It does not exclude any global cover.

A separate exhaustive diagnostic proves a simpler pair-floor test. For removing block B, an incoming block must contain every pair in B whose old count is5, equivalently the union of those pairs' endpoints. All275456 direct recounts agree. Of64 outgoing blocks,55 force all five vertices and hence allow no distinct replacement; two force no vertex. The pair-floor-only legal total is8750, with8608 cases arising from those two removals. Additional row checks reduce that count to8667 in the optimizer scan. The diagnostic's proof and damaged controls are in `pair-floor-replacement-characterization/`.

The next preparation uses this idea for a complete two-block replacement neighborhood of the saved H12/D29 representative. After removing two blocks and adding one, any pair deficit greater than1 rules out the branch; otherwise the second new block must contain the endpoint union of the remaining deficient pairs. The full neighborhood contains18,668,272,896 unordered two-out/two-in replacements. Only a separately checked complete pass can claim local closure; a timeout is inconclusive. Preparation is not an optimizer result. Fresh public-table checks failed: the old host did not resolve, and the current target page returned HTTP403 with an access challenge. Neither refreshes the earlier recorded bound. No verified64-block cover has been found.


The H12/D31 family shares62 blocks with the D32 input and preserves the exact same hole set. Its necessary-partition screen is empty, proving every relabeled old-core overlap is at most55. Independent screening also qualifies all four H12/D29 best ties; each has zero necessary partitions, pair minimum5, zero single/quad deficit and named overlaps[1,1,1,2]. All four ties are one replacement apart. Their receipts are in `soft-pair-hole-priority-relabel-novelty/` and `weak-pair-d29-relabel-screen/`. These partials are not complete covers.

Fresh frozen dependency sync checked17 packages. All369 package tests passed in258.70 seconds with the three existing SWIG warnings, and Ruff passed. The test transcript and receipt are in `hole-priority-checkpoint-validation/`; experiments have their own separate controls and runtime audits.


## Complete two-block neighborhood and a radius-four pilot (October 4)

The new pair-deficit support rule is necessary and sufficient for repairing the pair floor after two removals and one addition: a remaining deficit above1 is impossible to repair with one block, and otherwise the second new block must contain every endpoint of the remaining deficient pairs. Sorted removal and addition pairs give unique exact-distance-two neighbors. Independent controls checked all6885 support masks and139776 superset incidences,31 partial states,60 full states,230000 direct counter comparisons,130769 completion checks,29 invalid operations and92 dual-verified control families. The v2 recorder additionally rejects inconsistent support-bin and interruption accounting. Original frozen v1 source is preserved and was never launched.

The sole v2 pass from the pinned H12/D29 representative completed in4.21857 native seconds. It accounts for all18,668,272,896 exact-two-swap neighbors:18,667,163,216 fail the proved pair-floor reduction and1,109,680 receive full metric evaluation. Of those,413275 satisfy all declared weaker pair/core rules. Six neighbors improve the rank, all toH12/D28; one strict record and all six best ties were saved. No hole count improved and no cover was found. Independent runtime reconstruction checks each of the six distinct families with direct counts and both covering verifiers, with no exchange or hash aliases. It verifies the frozen source/loop/accounting evidence without repeating the entire enumeration. The result is only about this exact-distance-two neighborhood. The receipt in `weak-pair-two-swap-scan-v2-runtime-independent/postcheck.json` has SHA256 `c2922a53aae7a51154b2006f457d88df886ab115fa6b88993920d04c62eb8d41`.

A separate local CP feasibility model keeps all4368 block variables and every original soft-model domain/row, clears all objective and hint fields, and appends only overlap with the frozen D29 representative at least60 and exact holes at most11. Equal cardinality makes the overlap row equivalent to at most4 block replacements. The three other D29 ties lie one replacement away, so each radius3 neighborhood lies within this radius4 neighborhood; no path-legality assumption is made. The inherited model has no explicit hard quadruple rows, so its candidate metrics must keep actual D4 separate from the native scan's stricter legal filter.

Root's independent model gate compared the full unchanged5728-variable/14405-row prefix and checked both new rows, canonical center vector, absence of objective/hint fields, parameter-only seed change and frozen source/input hashes. Native OR-Tools optional-field getters can create empty messages; the audit and revised runner use field-presence checks to avoid changing the proto. Independent runner review found an interrupted JSON-write recovery bug in the unlaunched v1 preparation. V2 preserves the exact same model/parameters, fixes terminal-record recovery, and passes seven producer and six additional independent fake-process cases. Those recording-path fixtures are synthetic, not mathematical witnesses.

The sole v2 radius-four call (seed2026105201,300 seconds,four workers) returned UNKNOWN without a callback or feasible partial. Its producer result SHA256 is `e99bc1784200f8691f268435f9e7b64515cbd38ca0e2fd04854395bc69eecc59`; independent runtime postcheck passed with SHA256 `cbb8fc3d601ed2addb0ed2bf1a5009096866310d61680bc364a20cfb6f5d366e`. It confirms300.009194 native seconds, zero callbacks/vectors/families, empty solution and other repeated response fields, one native solve, unchanged hashes and no watchdog firing. This timeout does not exclude the radius-four neighborhood or imply a global lower bound. The next preparation is a separate bounded descent campaign using the unchanged one- and two-swap kernels, with explicit complete-pass and strict-improvement rules. No64-block cover has been found.


The sixH12/D28 ties were independently preserved, profiled and screened against every relabeling of the old core through the necessary-partition criterion. All six have zero necessary partitions and therefore overlap at most55 with every relabeled old core. Their pair-count histograms distinguish at least four isomorphism classes. Five change the actual hole set; the sixth keeps the D29 hole set and is one swap from the saved D31 family. The representative is four swaps from D31. These are different partial families with the same12 uncovered triples in count, not new covers. Sources and all six witnesses are in `weak-pair-d28-relabel-novelty/`, manifest SHA256 `d691cb2a5405e2fb8796455a6cf4d336e70aca000f362b536181c57ab1603f36`.
