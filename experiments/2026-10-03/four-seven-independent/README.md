```
Document:    Four Sevenfold Triple Reduction and Independent Model Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      7aae9670fd188fa1d785d00af740e844658dfb2d53bf329132c06a9c1e637e3e
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Complete conditional reduction

Assume a full C(16,5,3) cover of 64 distinct blocks, with degree 20 at every
point, and four triples of multiplicity seven. This is a conditional branch,
not a reduction of all possible 64-block covers.

Pair multiplicities satisfy λ≥5. The excess at each point is exactly
4·20−15·5=5. A sevenfold triple has internal pair multiplicities at least seven,
so its two internal pairs consume at least four excess units per anchor.
The previously checked heavy-hub argument gives four disjoint anchor triples,
each with a unique repeated outside hub; those hubs are distinct and outside
all heavy triples. Their twelve anchors and four hubs therefore partition all
sixteen points.

Relabel the four groups as (1,2,3;4), (5,6,7;8), (9,10,11;12), (13,14,15;16),
where the final label is the hub. At each anchor, internal pairs consume four
units and its hub pair consumes one. Consequently internal anchor pairs have
λ=7, anchor/own-hub pairs have λ=6, and every other pair touching an anchor has
λ=5. Each hub spends three units on its own anchors and has two left, entirely
on hub/hub pairs.

The hub-pair excess is thus a loopless multigraph of degree two on four vertices.
Exhausting all 3^6 edge-weight assignments gives six labeled graphs: three
four-cycles of unit edges and three pairs of disjoint doubled edges. The saved
certificate gives an explicit group permutation taking each graph to the
chosen cycle or matching representative. These are exactly two orbits under
simultaneously permuting the anchor groups and their hubs; no covering is lost.
No essentiality, local-family, or rotational assumption is used.

# Allowed blocks and pair counts

An internal anchor pair has λ=7, and its seven common heavy-triple blocks exhaust
all seven occurrences. Thus no block contains exactly two anchors of any group.
Every other block remains available. The full lexicographic list of 4,368 block
variables is retained; exactly 2,892 are fixed to zero.

There are 276 permitted blocks containing a heavy triple: for each of four
triples, choose two of the thirteen outside points, excluding the nine pairs
inside another anchor group. This gives 4·(C(13,2)−3·C(3,2))=276. Such blocks
cannot contain two heavy triples because six labels would be required.

The other 1,200 permitted blocks contain at most one anchor from each group.
The coefficient of x^5 in (1+3x)^4(1+x)^4 is 1,200. Broken down by anchor count,
there are 12, 216, 648, and 324 blocks with one, two, three, and four anchors.
Hence the complete permitted universe has **1,476 blocks**.

Cycle-case pair multiplicities have histogram λ5/λ6/λ7 = 92/16/12. The matching
case has 94/12/14. Both give pair incidence 80 at every point and total 640.
The selected covering must contain 28 heavy blocks and 36 nonheavy blocks.
In the heavy blocks, every anchor occurs ten times and every hub five times,
so their degrees in the nonheavy blocks are ten and fifteen, respectively.
These last identities follow because each heavy link contains every outside
point once, except its own hub twice.

# Stronger multiplicity and triangle counting

For any pair with λ=5, the sum of the multiplicities of its fourteen incident
triples is 15. Full coverage therefore permits precisely one double-covered
triple at that pair and no triple of multiplicity at least three.

Apart from the four heavy triples and twelve triples consisting of two anchors
and their own hub, every triple contains a λ5 pair in both hub cases. This is
also verified by direct enumeration of all 560 triples. The twelve own-hub
triples occur twice in their sevenfold links. Hence every nonheavy triple has
multiplicity one or two. The total of 640 triple incidences forces exactly
**four sevenfold triples, 56 double triples, and 500 single triples**.

Remove the twelve prescribed own-hub double triples. The remaining 44 distinct
double triples contain at most one anchor per group, and their pair counts must be:

| Pair kind | Demand among the remaining 44 triples |
|---|---:|
| Two anchors in the same group | 0 |
| Anchor and its own hub | 2 |
| Any other pair touching an anchor | 1 |
| Cycle hub edge / cycle hub nonedge | 4 / 1 |
| Doubled matching edge / other hub edge | 7 / 1 |

There are 400 candidate triples for this necessary triangle decomposition.
Its anchor degrees are seven and its hub degrees twelve. If z is the number
of all-hub triangles, the counts with zero, one, two, and three anchors must be
z, 18−3z, 12+3z, and 14−2z. The two λ5 hub nonedges in the cycle case, or the
four λ5 cross-matching edges in the matching case, imply z≤2. Thus z is 0, 1,
or 2. These are necessary arithmetic conditions, not a construction of blocks.
Any solver-based exploration of that smaller system requires an independently
checked witness or certificate before a mathematical conclusion is claimed.

# Independent model audit

`check.py` copies the root model source into ignored scratch, imports that
snapshot only to obtain each actual model, then independently reconstructs all
rows from raw combinations and the proof above. It does not use the production
pair-target or block-eligibility helpers as its oracle.

Both full-cover models have 4,368 Boolean variables in full lexicographic order
and exactly 3,593 unconditional linear rows: 2,892 forbidden-block equalities,
one size equation, sixteen point equations, 120 pair equations, four heavy
triple equations, and 560 coverage inequalities. There is no objective, hint,
extra assumption, or additional normalization in the audited full models.
Five damaged-row controls per case are rejected. The root candidate checker
rejects ten malformed or wrong-branch controls. No positive candidate-checker
path is claimed because no witness in these branches is known.

The full-model row audit says nothing about whether either model is feasible.
UNKNOWN or timeouts are inconclusive, and CP-SAT INFEASIBLE alone would not
be an independently checked theorem. The partial-search option retains the
full-cover branch restrictions and is not a complete model of arbitrary partial
coverings. This audit reconstructs the full-cover option only.

Run from the worktree root:

```sh
uv run python experiments/2026-10-03/four-seven-independent/check.py
```

`result.json` records the exhaustive hub-graph maps, block/triple counts, source
and model hashes, and damaged controls. Large model snapshots remain under
ignored `experiments/scratch/four-seven-independent-models`.
