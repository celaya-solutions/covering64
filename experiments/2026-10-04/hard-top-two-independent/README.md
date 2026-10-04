```
Document:    Hard Top-Two Independent Model and Runtime Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      083ed5d8f2413cdb2bc5f3e8435afc1e12648c2dd4767ac6a48b01db5c3fe46b
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent hard top-two model, runner and runtime audit

The frozen serialized model and separately frozen runner pass their independent gates. The sole root-launched 120-second run returned UNKNOWN with zero callbacks, zero solution vectors, no witness, and objective bound zero. The raw response reports 120.256684 solver seconds; the runner measured 120.256386 elapsed seconds. This bounded outcome is inconclusive.

## Exact model audit

The checker derives all 7,408 variable names/domains and 3,605 linear rows directly from the lexicographic 1-based block universe and bit-mask containments. The model has all 4,368 free Boolean block variables, 120 pair counts, 560 triple counts, 560 exact hole flags, 120 z variables, and 1,680 y variables. Pair counts have domain [5,64]; triple, z and y values have domain [0,64]. All four independently bound 60-block core caps are 55. The objective is exactly the sum of the 560 hole flags.

The rows comprise one cardinality equation, 680 exact count definitions, 1,120 hole-channel rows, 1,680 hinge rows, 120 top-two budget rows and four core caps. Every row coefficient, domain and enforcement literal is checked. Unexpected proto fields, duplicate coefficients, extra strategies, changed objective terms and changed hint positions are rejected. There are no fixed blocks, degree constraints, regularity assumptions, named partitions or additional symmetry rows.

The guidance contains only the 4,368 H49 block values, with 64 ones and 3,040 unhinted auxiliary variables. Independent recount gives 49 holes, D2max=74 and D2sum=170. Its canonical z/y extension violates exactly 74 budget rows. The projection proof below shows that no other auxiliary extension can repair that same block assignment, so this is infeasible guidance rather than a feasible warm start.

## Exact projection and omitted single rows

For a pair P, write p=c(P), t_x=c(P union {x}), and B=3p-12. The compact rows are

```
0 <= z <= 64,  0 <= y_x <= 64
y_x + z >= t_x  for each of the 14 distinct outside positions
2z + sum_x y_x <= B.
```

For any two distinct positions a,b, these rows give t_a+t_b<=2z+y_a+y_b<=2z+sum(y)<=B. Thus they imply every one of the 91 explicit strong rows for P.

Conversely, set z to the second-largest position count and y_x=max(0,t_x-z). Then 2z+sum(y) is exactly the sum of the two largest positions. This remains true when values tie: positions remain distinct, and only values strictly above z contribute to y. The variables stay in [0,64]. Integer counts give integer witnesses; the same argument works for real-valued counts. Therefore the existential projection equals the full explicit strong-row system, including its continuous local relaxation.

Exact block-count definitions give sum_x t_x=3p. Summing the 13 strong rows involving a fixed position a and adding the zero equality -3p+sum(t)=0 yields 36p-12t_a>=156. Dividing by 12 gives 3p-t_a>=13. Thus the omitted 1,680 single-triple rows are implied even over reals.

The analytic proof is supported by 31,521 compatible integer profiles, 3,060 count histograms each minimized over all 65 possible integer z values, 98,304 tied-position profiles, and 14 coefficient checks of the single-row implication. Twelve independently damaged serialized models are rejected. These finite checks support the algebra; they do not enumerate all block families.

## Runner and outcome

The final run gate binds the model preparation manifest, model, parameters, H49 guidance, runner and separate runner manifest. The runner has one solve call, fixed at 120 seconds, four workers and seed 2026104601. It refuses an existing run and saves every delivered callback, including ties, plus any feasible final vector. It saves all 7,408 actual solver values and the separate canonical extension. Noncanonical z/y values are legitimate when they satisfy all rows and are never forced to match the canonical extension.

The runner recounts the exact first 5,608 values, actual pair deficits, both old deficit screens, all core caps and the global profile. It runs both covering verifiers before accepting a holes-zero stop. Positive-hole feasible hints do not stop this holes-minimizing run. Independent controls reject seven incorrect gate variants and three invalid full vectors. No actual feasible hard-model family was available for a positive end-to-end control; none was invented.

The independent runtime checker rechecks the entire serialized model, full source and artifact bindings, raw response, logs, time, callback count and final state. This run has no vector to verify, so it made no cover-verifier calls. For future feasible vectors the checker accepts legitimate noncanonical z/y values by checking every inequality, and independently checks each candidate and canonical extension.

`model-gate.json` is the model-only receipt. `gate.json` is the separately bound run gate. `postcheck.json` is the runtime receipt. The audit called no optimizer and did not alter the frozen producer. UNKNOWN and timeouts are inconclusive; a CP-SAT infeasibility status would still not be an independently checked theorem.
