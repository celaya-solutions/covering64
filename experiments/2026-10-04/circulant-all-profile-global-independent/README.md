```text
Document:    Independent Complete Circulant Profile Model Gate
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      957e1e09cb86b2481cee3a3329cbb08aa655bbe2cce847ccedbdb3cbd7bf13fa
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent complete-profile model gate

Decision: GO for the single frozen call bound in gate.json. The audit checks all 15
preparation pins, all serialized constraints, the exact parameter record, the explicit
profile-orbit reduction, and mocked launcher behavior. No solver or real subprocess was
launched. Root alone owns the authorized 300-second, four-worker call with seed
2026106501, a 310-second watchdog, and five-second termination grace.

## Why the profile reduction preserves the named graph problem

Fix the graph on labels 1..16 given by differences {1,3,8,13,15} modulo 16. Consider
an exact 64 cover whose pair multiplicity is six on its 40 edges and five on the other
80 pairs. Let h(T) be triple multiplicity minus one. Covering gives nonnegative integral
h, with total 80 because 64 blocks contribute 640 triple incidences to 560 triples.
For a pair, summing h over its 14 containing triples gives three times its block
multiplicity minus 14: four on graph edges and one on nonedges.

The graph is triangle-free, so each triple contains at most two graph edges. Summing
h across graph-edge incidences gives 40×4=160, which equals 2×80. Equality forces every
positive h triple to contain exactly two graph edges. Its remaining nonedge has total
excess one, so h can only be one. Thus every such cover has an 80-path excess profile
with exactly one center chosen for each nonedge.

The independently checked tight-cut bound forbids 32 paths and forces 32 others. The
remaining 48 nonedges each have exactly two allowable centers. The prior independent
integer enumeration exhausts this 48-bit arithmetic system and finds exactly 1,300
profiles. This audit pins that completed enumeration, its independent checker and
receipt, and its input/output hashes. It does not rerun or overwrite that receipt.
Every decoded profile is recounted against the exact pair demands here.

This audit independently verifies all 32 supplied label permutations preserve the graph
and form a group. For each of the 52 representatives, it directly transforms all 80
profile triples under all 32 maps, matches the resulting masks to the saved orbit, and
checks disjointness, stabilizer size, and union over all 1,300 masks. It saves one explicit
map from a representative to every mask in profile-orbit-maps.json. Every representative
is the minimum mask of its checked orbit.

If a cover realizes a nonrepresentative profile, apply the inverse of its saved map to
every label of every block. This bijectively permutes the complete lexicographic block
universe, preserves distinctness and covering, preserves the named pair graph, and takes
the excess profile to the chosen representative. The converse is immediate because a
representative is itself one of the 1,300 profiles. Therefore using the 52-row table
preserves existence for this named pair graph. No cover is required to be invariant
under any permutation. This is not an unrestricted reduction over all possible pair
graphs, and no cover orbit classification is claimed.

## Exact serialized model

The model contains 4,368 free Boolean cover-block variables in lexicographic order,
followed by 48 free Boolean center-choice bits. Its 562 constraints are one exact 64
cardinality equation, all 560 exact triple equations, and one positive allowed table.
There are 32 fixed demand-two rows, 432 fixed demand-one rows, and 96 conditional rows.
For each choice bit z, the first center's row is B+z=2 and the second is B−z=1.
Both values of z are checked algebraically against the intended excess indicator.
Every triple row contains all 78 block carriers exactly once with coefficient one.

The allowed table has 48 direct bit columns with coefficient one and offset zero, and
exactly 52 bit vectors in the independently checked representative order. It has no
guard and is not negated. No variable domain is fixed, and there is no objective, hint,
assumption, serialized symmetry, custom search strategy, local link, neighborhood, or
additional block constraint.

Thirteen damaged model controls are rejected, including fixed variables, reversed
selector sign, changed table value/column/offset/polarity, extra table cell, guarded
table, added link row, objective, hint, and assumption. Eight mocked launcher scenarios
pass: normal call, terminate after watchdog, kill after grace, nonzero child, missing
child, invalid gate, mismatched manifest, and existing child output. The normal case also
rejects relaunch. Every process and solver operation is mocked during those controls.
Ruff passes.

Any feasible result must provide a 64-block witness, match the selected table profile
and named pair multiplicities, and pass both cover verifiers. UNKNOWN is inconclusive.
CP-SAT INFEASIBLE without a separately checked proof is not an independent theorem.
The audit establishes encoding and reduction correctness, not solver success or a
mathematical exclusion.
