```text
Document:    Independent Skeptical Review of the C(16,5,3) Campaign
Version:     v1.2.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      13f7bcc8d181e6bf23835aac82f23744353417cce324069a2841fbc0745189bc
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent skeptical review

This review reads repository revision `c31aea40bb52dddd43532e91c3d62558fcf25cde` and the separately supplied live continuation snapshot. It runs no covering solver and does not replay all older certificates. The inventory below reports the scope claimed in the saved records; the primary-source checks and Clebsch counting argument were checked independently here.

## Current result and public evidence

No verified 64-block cover is present in the reviewed record. The general best has 557 of 560 triples. The live campaign has a six-hole state passing its heavy-profile filter; the committed checkpoint's eight-hole point-essential state is an older, narrower benchmark. These are different search classes and should not be ranked as though their restrictions were identical.

At 2026-10-03 22:11 UTC, the public Covering Repository search returned the row `(v,k,t,m)=(16,5,3,3)`, 65 blocks, lower bound 61, creator Rade Belic, source Dan Gordon Covering Repository, date 06/08/1997. Its definition with m=t is the ordinary covering number. The data support the current table statement **61 <= C(16,5,3) <= 65**, not a claim that 64 is impossible.

- Gordon's [maintainer page](https://dmgordon.org/covering-designs/) explicitly directs readers to [Covering Repository](https://coveringrepository.com/) for the old collection and newer improvements. Both pages were retrieved successfully. The legacy [LJCR target](https://ljcr.dmgordon.org/cover/show_cover.php?v=16&k=5&t=3) failed DNS resolution.
- The [target query](https://coveringrepository.com/systems.aspx?v=16&k=5&t=3&m=3) and direct history/download requests returned HTTP 403. The same public [search page](https://coveringrepository.com/systems.aspx) worked through its ordinary HTML search form. The successful request posted v=16, k=5, t=3, m=3 with the page's own form fields. Its returned row links to [download 108633](https://coveringrepository.com/download_system.aspx?id=108633) and [history 110841](https://coveringrepository.com/history.aspx?id=110841). Neither linked resource was independently downloaded in this review.
- J. L. Allston, R. W. Buskens and R. G. Stanton, *An examination of the non-isomorphic solutions to a problem in covering designs on fifteen points*, JCMCC 4 (1988), 189-206, [original publisher PDF](https://combinatorialpress.com/article/jcmcc/Volume%2004/vol-004-paper%2015.pdf), was retrieved and visually read on printed pages 189 and 204. Theorem 12 on p.204 states four distinct minimal (2,4,15) covering designs, B3, B4, D1 and D2. The introduction gives the recursive incidence inequality and the value formula for four-point pair coverings. Thus the project's four-link classification recovers published mathematics; it is not a new global C(16,5,3) result.

Small retrieved sources and request metadata are in `experiments/2026-10-03/independent-primary-sources/`. The successful target response SHA256 is `97714ccfaa1f855c0f3489e191b160ada34347884b730cdc12008872926f6a2f`; the primary PDF SHA256 is `dd229074b271c22475bae2993daa9cf089a988f3670237c742e22246dcb93e8d`. These checks are a bounded source review, not an exhaustive literature search.

## Completed and active methods

| Method | Recorded work | Scope and independent assessment |
| --- | --- | --- |
| Belic core and nearby completions | 60-block core; 248,832 completions to size65; two derived65 covers share that core up to relabeling | Relabeled or newly completed examples can be the same search basin. |
| Core removals through four | 8,337 representatives cover all487,635 four-removal sets, with rational dual certificates | Recorded independent certificates justify at most55 retained core blocks, including relabeled core cuts. They do not exclude all64 covers. |
| Deeper core neighborhoods | 909 selected five-removal classes,33 six-removal and100 seven-removal kernels independently excluded;155 eight-removal CP kernels infeasible with audited inputs | Finite listed neighborhoods only. Eight-removal solver statuses do not have the same proof standing as independently replayed trees. |
| Regular group actions | 17 explicit regular permutation actions, each all226,387,980 four-orbit selections | Exhausted within those actions. They are not necessarily17 distinct groups, and group-invariant covers are a restriction. |
| Smaller cyclic and orbit heuristics | Twelve bounded cyclic CP searches; four orbit tabu pilots | Already tried, inconclusive. Renaming or reducing a cyclic family is not automatically a new direction. |
| General local search and repairs | Weighted local search, tabu, larger replacement neighborhoods, trade walks, LP screens,600-second broader repair | General best remains three holes; near-three repair states retain the same60-block core. More time or another seed alone is not methodological novelty. |
| Global and degree branches | CP-SAT, native-cardinality SAT and SCIP; degree19 or regular20 split; exact core cuts | All bounded global runs inconclusive. Degree split is complete, but solved subfamilies are not. |
| Degree19 links and double hubs | Four known link classes reconstructed;576 second links ->270 ordered reps ->196 after anchor swap; six fixed32-block families excluded | Classification is known mathematics. The double-hub family still leaves190 of196 cases without these local certificates, and covers only the stated shared-six-block configuration. |
| Point-essential regular search | Private-triple reduction, pair-feasible regular seeds, atomic cycles through length8, reservoir diversification | Complete-existence reduction is across both degree branches. Its restricted near-cover score is not the unrestricted best score. |
| Heavy triples and local13 families | Heavy-count restrictions; exactlythree local13 families under stated hypotheses;13 first-family representatives;13 bounded CP runs | Already completed classification and ongoing extension route. Templates, trades and additional local-family samples would overlap the active campaign. |
| Current structured campaign | Four/six local-family trades, residual-pair and packing cuts, corrected five-heavy-triple obstruction, general heavy-profile heuristic | Current independently recounted eligible seed has six holes. A three-hole state was rejected as an eligible escape seed after a threshold error was found and corrected. |

The recovery record explicitly says the earlier workspace and original raw artifacts were lost. Fresh reconstruction results must remain separate from historical summaries. Source revision, archived model, actual constraints and evidence type matter more than a method name.

## What would be distinct

A new representation of the *whole pair/triple excess structure*, tested without retaining the Belic core or fixed local families, is distinct from the listed repair campaigns. Selecting an admissible pair-excess graph first and then solving for actual blocks is one such construction route. A graph choice is a restriction unless every admissible graph has been classified and every class checked.

A canonical augmentation that exhausts a newly proved complete family could also be new. A bounded run under a new symmetry group, an incumbent histogram, or a chosen geometric template does not gain completeness from its name. Similar block counts, relabelings, or invariant fingerprints alone do not establish a new basin; explicit isomorphism maps or a separating invariant are needed.

The low-cost Clebsch pair-excess probe is a reasonable first structural experiment. It avoids prescribed block orbits and leaves all4,368 block variables available. Its immediate value is a clean feasibility question and a small independently checkable encoding, not a promised improvement.

## Independent Clebsch derivation

Let G be the Clebsch graph on16 points: degree5, no triangles, and exactlytwo common neighbors for each nonadjacent pair. Fix pair multiplicities lambda(p,q)=6 on its40 edges and5 on its80 nonedges. These targets imply point degree20, because the15 pair multiplicities at each point sum to80 and each incident5-block contributes4. They imply64 blocks by the degree sum.

For a complete cover write h(T)=m(T)-1, its triple excess. There are640 total triple incidences, so sum h=80. For each pair pq, sum of h over its14 third points equals3*lambda(p,q)-14: four on edges and one on nonedges. Consequently the total G-edge incidence in h is40*4=160.

Every triple of a triangle-free graph contains at mosttwo G edges. Since h is nonnegative,160 <=2*80 is equality. Every triple with positive excess must therefore induce a two-edge path, P3. Each P3 has exactlyone nonedge, whose excess demand is one; hence h(T) is either zero or one. Every non-P3 triple occurs exactlyonce, and each of the160 P3 triples occurs once or twice. Each nonedge has exactlytwo common neighbors, so exactlyone of its two corresponding P3 triples is doubled. This proves the proposed exact triple bounds within the fixed pair profile.

An independent enumeration used the16 even subsets of a five-element set, adjacent when their symmetric difference has size4. It checked all4,368 five-point subsets. Their eleven `(edge count, P3 count, sorted degree sequence)` signatures are recorded below. There is no elementary contradiction from their aggregate edge/P3 counts: a selected cover would have240 of each incidence, and both positive and negative per-block differences occur.

| Edges | P3s | Sorted degrees | Available blocks |
| ---: | ---: | --- | ---: |
| 0 | 0 | 0,0,0,0,0 | 16 |
| 1 | 0 | 0,0,0,1,1 | 320 |
| 2 | 0 | 0,1,1,1,1 | 240 |
| 2 | 1 | 0,0,1,1,2 | 480 |
| 3 | 2 | 0,1,1,2,2 | 960 |
| 3 | 3 | 0,1,1,1,3 | 160 |
| 4 | 3 | 1,1,2,2,2 | 480 |
| 4 | 4 | 1,1,1,2,3 | 960 |
| 4 | 6 | 1,1,1,1,4 | 80 |
| 5 | 5 | 2,2,2,2,2 | 192 |
| 5 | 6 | 1,2,2,2,3 | 480 |

Two selected blocks may intersect in three points only when that triple is a P3. If they intersect in four points, every triple in that intersection must be a P3, forcing an induced four-cycle. These are consequences of the triple bounds, not extra assumptions. No assertion is made that every row is one automorphism orbit.

## Required audit boundaries

1. This graph profile must be labeled a restricted construction experiment. No derivation says every regular64 cover has simple0/1 pair excess or Clebsch excess. The degree19 branch is also outside it.
2. All4,368 distinct5-block variables must retain lexicographic order and1-based external labels. Check graph adjacency against an independent construction, not imported producer edges.
3. Fixing the graph removes arbitrary S16 relabeling freedom. Do not force an arbitrary selected block to {1,2,3,4,5}; a valid normalizer would need a complete orbit argument under graph automorphisms. Do not silently retain only some of the eleven block signatures.
4. The P3 derivation uses complete coverage. A positive-hole model cannot reuse non-P3=1 and P3<=2 as if they followed from pair targets alone; the excess h can then be negative. Explicitly separate full-cover feasibility from any later heuristic relaxation.
5. Optional point-essential constraints preserve existence only in conjunction with the degree19 branch. They are not an equivalence for this fixed Clebsch pair profile; a point replacement changes the pair profile. Omit them when claiming to decide all covers with this graph profile.
6. Feasible output needs both required covering verifiers, plus independent pair-profile recount. UNKNOWN and a timeout say nothing about nonexistence. CP-SAT INFEASIBLE is a solver result; an independently checked proof is needed for a certified family exclusion, and that exclusion would still be conditional on the graph profile.
7. Model integrity checks should reject an altered edge, missing pair equation, wrong triple bound, omitted block, duplicate labels and changed variable ordering. Checking metadata or hashes alone does not test mathematical completeness.

## Follow-up encoding audit and balanced cuts

The standalone checker `scripts/check_independent_clebsch.py` parses archived text-protobuf models using the Python standard library. It imports neither the producer nor OR-Tools and invokes no solver. It independently constructs the four-dimensional cube with its antipodal diagonals and maps that graph to the archived labels. Both the free Clebsch model and the fixed seed0 profile model pass its complete comparison of4,368 variables,697 constraints and113,568 nonzero coefficients. Their archived model hashes match their result records. The free model and the fixed seed0 model both report UNKNOWN, which remains inconclusive.

Forty-eight focused tests pass, including malformed graph/profile inputs, altered coefficients, omitted rows/variables, changed ordering, hidden enforcement/objective fields, unsupported protobuf syntax, wrong bounds and a fixed-versus-free model mismatch. These are mathematical and encoding controls, not merely hash checks. The graph model contains no fixed block, point-essential cut or partial-cover mode. The initial generator samples satisfy the independently counted profile pair loads. The full recipe-certificate replay below subsequently replaces the sample-only check for its stated finite family.

For any full regular20 cover, put E(pq)=lambda(pq)-5, a nonnegative weighted graph of degree5. For a partition S and its complement, each block with a points in S has10-(3/2)*a*(5-a) triples internal to the two parts. Summing over64 blocks gives640-(3/2)*(5*|S|*(16-|S|)+Ecut). It must be at least binomial(|S|,3)+binomial(16-|S|,3). Thus an8+8 cut satisfies Ecut<=32; a7+9 cut satisfies Ecut<=97/3, hence at most32 integrally and at most31 by the odd weighted-degree parity. These inequalities are necessary throughout the regular branch, without assuming a simple or Clebsch excess graph. They immediately exclude a simple degree5 bipartite excess graph, whose bipartition has cut40.

For Clebsch, the6,435 unordered8+8 cuts have histogram {16:70,18:1440,20:1560,22:1920,24:600,26:640,28:200,32:5}. Each side of the five tightcuts induces a matching, so no allowable P3 is internal to a tightcut. Saturation alone gives no contradiction. Complete arithmetic and model audit results are saved in `experiments/2026-10-03/independent-geometry/independent-model-audit.json`.

## Independent profile-orbit certificate replay

The checker independently rebuilt all1,024 profiles in the fixed regular-tournament recipe. Its construction starts with common-neighbor squares of the independently built four-cube graph, not the producer's binary-generator square construction. Every rebuilt profile has the required80 triples and pair loads, and matches its saved canonical hash.

The80 explicit point maps are distinct graph automorphisms, contain the identity and are closed under composition. Recomputing their actions yields16 disjoint orbits: twelve of size80 and four of size16. Their member lists cover all1,024 recipes exactly, and every saved profile-to-representative map was replayed. The16 saved seeded representatives were independently recounted and their normalizing maps reach the claimed orbits. Four damaged-certificate controls repair the outer hash before checking, and still reject an omitted member, false map, damaged profile hash and nonautomorphism.

This proves the finite recipe certificate under the stated80-element action. It is not an enumeration of all admissible Clebsch excess profiles or all64-block covers, nor a proof that the16 representatives are pairwise nonisomorphic under every possible relabeling. The orbit certificate body hash is `9c1ef64b3ff11736d87bc5636fb8cd5aabad58996b8d20ec9cf54b7e83fe8384`. The audit report and saved16-seed profile input contain reproducible independent recount results. No solver was invoked by this reviewer.
