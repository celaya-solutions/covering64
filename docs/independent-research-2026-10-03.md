```text
Document:    Independent Construction Routes for C(16,5,3)
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      4463aeee6c98d141181c2eb7a0b842b3fbd7c4c78c16f29e7a7d75b950948b49
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Result and scope

**No verified 64-block cover was found.** No global lower bound was proved.
The live public table still records **61 <= C(16,5,3) <= 65**. The existing
557/560 partial cover was not improved by this investigation.

Work began from committed research revision
`c31aea40bb52dddd43532e91c3d62558fcf25cde`, on the separate branch
`codex/independent-geometry-20261003`. Both existing worktrees were read-only.
The active session's newer continuation was copied as a dated evidence snapshot;
its agents and processes were not contacted. All new code, logs, and witnesses
are in this worktree. Solver runs were sequential, with one worker each.

Three agents had separate duties: geometric constructions, excess-count
mathematics, and skeptical review with independent source/model checks. The
root selected experiments, ran solvers, and checked the combined evidence.

# Compact inventory before choosing a route

These are the scopes reported by the saved checkpoint, not claims that every
historical certificate was replayed here. The recovery record identifies lost
historical artifacts; none was recreated or invented.

| Already explored | Saved outcome or scope |
| --- | --- |
| Repairs and completions around the Belic 60-block core | Many 65-block completions; general best 64 still has three holes. Checked certificates limit any 64 cover to at most 55 blocks of that particular core, including relabelings. |
| Core-removal neighborhoods, LP duals, finite trees | Numerous local exclusions. Selected deeper CP results lack an independent proof. None settles unrestricted existence. |
| Seventeen regular permutation actions; cyclic/orbit searches | Specified invariant families exhausted or bounded searches timed out. These are restricted families. |
| Unrestricted/degree-split CP, SAT and SCIP | Bounded inconclusive searches. Degree19 links have four classified types; regular 20 is a separate branch. |
| Fixed links, double hubs, point-essential regular models | Several independently checked local exclusions and many timeouts. |
| Current other-session campaign | Three local 13-point families, 13 first-family representatives, heavy-triple restrictions, trades and residual-pair cuts; an eligible six-hole seed. This active campaign was deliberately avoided. |

The fuller inventory and live source checks are in
[the skeptical review](independent-skeptical-review.md).

# Three materially different approaches

| Route | What changes | Assumptions and small test |
| --- | --- | --- |
| **Pair-excess geometry, selected first** | Prescribe pair counts using the folded five-cube, then decompose exact triple demands into five-blocks. No incumbent blocks or block-orbit invariance. | Restrict pair counts to 6 on its 40 edges and 5 elsewhere. Test the unrestricted excess choices within that graph, then one explicit excess pattern. |
| **Eight-pair partition** | Place all repeated triples on triples containing one of eight fixed pairs. This is a global support condition on excess, not a fixed point link. | Every one of 448 transversal triples occurs exactly once;112 other triples occur at least once. First test forbids block type2111, forcing 32 blocks of type221 and 32 of type11111. |
| **Inversive-plane mother design** | Start from a triple partition into 48 circle pentads and 20 line tetrads in AG(2,4), then replace circles with line extensions. | First prove whether one extension per line can reach64. Then permit any of 240 line extensions together with 48 circles, a288-block domain. This domain is a construction restriction. |

The first route was selected because counting converts inequalities into exact
triple demands while leaving all 4,368 five-block variables available. The other
two change the starting combinatorial object, rather than the random seed or
solver used by an existing campaign. None is an exhaustive reduction of all
C(16,5,3) covers.

Primary source context includes the current maintainer's
[covering-design page](https://dmgordon.org/covering-designs/), the
[Covering Repository](https://coveringrepository.com/systems.aspx), and
[Brouwer's graph page](https://aeb.win.tue.nl/graphs/Clebsch.html). The latter
explicitly distinguishes the degree10 Clebsch graph from its degree5 complement;
this report always uses the **(16,5,0,2) folded five-cube**. The geometry and
partition proposals, references, proofs, and access limits are detailed in
[the construction note](independent-construction-ideas.md). They are proposals
derived here, not claims that a source supplies a 64-block witness.

# Strongest structural results

For a regular 64-block cover, write `e(uv)=lambda(uv)-5` and
`h(T)=mu(T)-1`. Pair excess is a nonnegative weighted graph of degree5 at every
point. Triple excess satisfies

```
sum h = 80;   degree_h(u) = 15;   codegree_h(uv) = 1 + 3e(uv).
```

If the pair-excess graph is simple and triangle-free, counting its edge
incidences in the80 excess units forces every repeated triple to be an induced
two-edge path. Its single nonedge has excess demand1, so its multiplicity is
exactly 2; every other triple occurs exactly 1 time. For the folded five-cube,
each nonedge has two possible path centers.

The team constructed24,576 labeled excess patterns without a cover solver,
using regular tournaments on five directions and orientations of ten four-cycles.
They reduce to16 representative tests under explicit graph relabelings. This is
complete **within that construction recipe**, not a classification of all
admissible excess patterns or all covers. These patterns satisfy the arithmetic
requirements; they are not five-block coverings. See
[the excess derivation](independent-excess-ideas.md) and its replayable orbit
certificate.

A further necessary condition applies to the entire regular branch, with
weighted pair excess allowed: an8-versus8 cut has excess at most 32; a7-versus9
cut has excess at most 31. If a block meets one side in a points, its number of
internal triples is `10 - 3a(5-a)/2`. Summing and requiring all internal triples
to be covered gives these bounds; the7-point cut also has odd excess parity.
This immediately rejects bipartite5-regular pair-excess graphs. The folded
five-cube passes: exactly five unordered balanced cuts attain 32. Passing these
conditions does not imply that a graph extends to a cover.

The inversive experiment gives a checked **67-block minimum for the pure recipe
with exactly one extension of each of the 20 lines**. A removed circle has ten
triples, requiring all ten of its secant lines to serve it. Every pair of
removed circles has a shared secant that cannot serve both. Thus at most one
circle can be removed, leaving at least 47 circles plus 20 extensions. All1,128
circle-pair obstructions were reconstructed, and an explicit67-block example
attains the bound and passes both covering verifiers. This says nothing about
the larger288-block pool or arbitrary covers.

# Recorded budgets and results

| Experiment | Seed | Limit, one worker | Result |
| --- | ---: | ---: | --- |
| Folded-five-cube pair profile, excess choices free | 640301 | 120 seconds | UNKNOWN; no witness |
| Same pair profile, constructed excess seed 0 | 640302 | 60 seconds | UNKNOWN; no witness |
| Eight-pair support, block type2111 forbidden | 640303 | 120 seconds | UNKNOWN; no witness |
| Broader circle-and-line domain | 640304 | 120 seconds | UNKNOWN; no witness |

The first two timeouts did not justify simply lengthening the same search.
The subsequent probes changed the combinatorial restriction. UNKNOWN is
inconclusive; no statement here treats it as evidence of impossibility or
assumes that more runtime would succeed.

The four runs used 420 seconds of scheduled solver time in total. The final
pool run explored more than 22 million branches but still returned UNKNOWN;
that search effort is not an exclusion certificate.

# Evidence and next experiment

The evidence directory is `experiments/2026-10-03/independent-geometry/`.
It retains seeds, budgets, base revision, Python/OR-Tools versions, solver logs,
model hashes, exact source snapshots, intermediate profiles, and verifier
reports. Raw solver models remain local and ignored by Git; they can be rebuilt.
The source snapshot, rather than a later edited working file, is authoritative
for each recorded run.

Final checks passed 267 tests and `uv run ruff check .`. Dependency setup used
`uv sync --frozen`. The matrix and orbit audits run without a covering solver.

The independent graph-model checker reconstructs the graph by a different
binary representation and verifies all 4,368 variable names/domains and all 697
constraint rows. The partition audit independently rebuilds every row and
checks the type-count identity. Damage controls test missing or altered
constraints, coefficients, ordering and invalid profile inputs. The known65
control passes both covering verifiers; deleting a block, duplicating a block,
and damaging a label are rejected. The67 control is validation evidence only.

The most focused next test is exact decomposition of the remaining 15
representative tournament excess profiles, with a small fixed budget and
residual-capacity branching. Seed0 already timed out. A complete checked
rejection of all 16 would reject only the tournament recipe. Another step would
allow more general balanced square choices, which describes all excess
patterns for the fixed graph but still restricts the pair profile. Neither
step has evidence guaranteeing a construction. The pure one-extension-per-line
recipe should not receive more search time; its obstruction is already proved.

No result was published, no researcher contacted, and no branch merged or pushed.
