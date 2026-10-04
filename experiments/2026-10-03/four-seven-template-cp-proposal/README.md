```text
Document:    Boolean Heavy-Link Template CP Equivalence and Prototype
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      e9d317ef26a26adf6577f2a7099689c77b4485a103fb55c0d9834e99e3a84bc7
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Boolean heavy-link template extension

This prototype appends complete surviving-link choices to the two already audited regular four-sevenfold bases. The builder itself makes no solver calls; two separately logged bounded pilots are now complete. Matching has 55,528 Boolean variables; cycle has 104,848. Both retain the original 4,768 variables, including all 4,368 lexicographically ordered block variables, and all original 4,270 constraints and other protobuf fields.

For each of four heavy anchor triples, add one Boolean selector for each complete transported surviving link: 12,690 for matching and 25,020 for cycle. Exactly one selector is true. Each of the 69 admissible outside-edge block variables equals the sum of selectors whose template contains that edge. The nine remaining outside-edge blocks per group were already forbidden in the original base. The four exactly-one rows replace the audited LP simplex equations; all 276 marginal equations are copied exactly. Total constraints are 4,550.

## Two-way projection proof

Forward: let a normalized regular four-sevenfold cover satisfy the original base. Each heavy anchor triple has a seven-edge link. By the independently audited complete catalog and checked exclusion chain, its link is one of the surviving transported templates. Select that template for each group. All exactly-one and marginal equations hold. Existing auxiliary variables keep their original values.

Reverse: let an integer assignment satisfy the extended model. The original base is preserved verbatim. In each group, exactly one selector is true; the marginal equations force all 69 admissible heavy block variables to equal that complete template's incidence vector. The nine inadmissible edges remain zero. Projection therefore satisfies the original base and the catalog restriction; no nonheavy block receives any new restriction except consequences of these original constraints and exact heavy marginals.

Thus the extension preserves precisely the original base's integer solutions that have surviving complete heavy links. Catalog completeness and prior exact exclusions establish that every valid normalized regular four-sevenfold cover remains. This is conditional on that branch and its already audited reductions, not an unrestricted encoding or lower-bound proof. It does not impose cover invariance under any relabeling.

## Continuous selectors

Boolean selector domains are convenient for CP propagation but are unnecessary for the integer projection. If selectors are nonnegative, sum to one, and every heavy block marginal is binary, then a zero marginal forbids positive weight on every template containing that edge, while a unit marginal forbids positive weight on every template omitting it. Every positively weighted template therefore equals the chosen entire incidence vector. Because the audited catalogs contain distinct templates, exactly one weight is one. This also justifies a separate MIP engine with continuous selector columns.

## Optional whole-branch symmetry

In the m4=1 subcase, the unique block containing all four hubs is H union {a}, where H={4,8,12,16} and a is an anchor. A hub-graph automorphism moves a's group to group 0; a permutation within its anchor triple moves a to 1. Thus this entire subcase can be normalized to contain {1,4,8,12,16}.

Subsequent first-heavy-link canonicalization may use the group-0 stabilizer while fixing 1: its action on the outside-edge universe has an extension acting identically on {1,2,3}, so that restriction loses no outside-edge action. This proves completeness for the whole m4=1 branch. The initial group transport may change an old fixed-first-link representative; this normalization must not be used to combine exclusions within each old representative. The optional normalization is not implemented in this prototype.

## Evidence and limits

`manifest.json` hashes both complete frozen protos, their original bases, the builder and all audited matrix/catalog inputs. Raw protos are in `experiments/scratch/four-seven-template-cp-v1.0.0-prepared`. The builder validates each CP model and checks complete original protobuf preservation. The independent extension audit passed both models and rejected 20 damaged controls before the pilots. The first preparation attempt stopped before producing a model because CP infinite bounds use int64 sentinels while LP JSON uses null; the comparison now normalizes those representations.

## Completed whole-branch pilots

The matching pilot used seed 2026103701 and ended UNKNOWN after 301.522520 seconds. The cycle pilot used seed 2026103702 and ended UNKNOWN after 300.277008 seconds. Both had an exact 300-second solver parameter and eight workers, with only one CP process running at a time. These small elapsed overruns include solver shutdown. Neither returned an integer solution.

`collect.py` independently parsed both saved solver responses and parameter protos and checked status, time, counters and all artifact hashes without rerunning a solver. `pilot-audit.json` passed. `pilot-evidence.json.gz` preserves the complete responses, parameters, environment, frozen model manifest and encoding audit in 13,002 bytes. UNKNOWN is inconclusive; no exclusion follows. The pilots deliberately retained the audited 106-exclusion catalog version while the later 108-exclusion chain remained separate.
