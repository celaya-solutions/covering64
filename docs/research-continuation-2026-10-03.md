```text
Document:    C(16,5,3) Continued Research Checkpoint
Version:     v1.3.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      115647f1f2a915608cf625bf9e3f0599c6d09c7f45ea07e7556dcac3a64e6188
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Research continuation

No verified 64-block cover has been found. The strongest current first-link
screen has 102 independently checked exclusions out of 258 cases in the regular
four-sevenfold branch: 27 cycle and 75 matching. The remaining 156 are open.
This is a branch result, not a global lower bound.

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

The completed model changes passed `uv sync --frozen`, 306 tests plus 10 subtests,
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
