```
Document:    Radius-Four Feasibility Repair Preparation
Version:     v2.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      cbe5f741f18249a774e8383e9af26116848845e05a0eada3eeb7d485aa59d437
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Conditional local repair, not yet run

This v2 preparation preserves the unlaunched v1 folder. The runner now catches an incomplete child terminal JSON file, records that error, recovers complete saved candidate receipts, and still writes a terminal timeout/error result. Hint checks and vector validation avoid creating empty protobuf fields. Fake-process controls exercise ordinary completion and interrupted writes, including terminate and kill paths, without invoking CP-SAT; a separate control checks that vector validation leaves the model unchanged.

This preparation makes no solver calls. Root alone may launch the single bounded pilot after the two-swap scan reaches its terminal state and only if that scan supplies no candidate with at most 11 holes. The independent gate must bind the final manifest, model, parameters, and runner hashes and return `GO`.

The center is the independently checked D29/H12 representative `swap-881-1142.txt`, SHA256 `44e0ee69fb32f37eed00955e25c699a72430d85871ca03a348c0bf572edb7a0a`. It has 64 distinct blocks and 12 uncovered triples, so it violates the new hole bound. Its full vector is saved only as a diagnostic. All old solution hints are removed; no complete feasible hint is claimed.

The frozen hole-priority soft model keeps every one of its 4,368 lexicographically ordered block variables, all 5,728 variable domains and names, and all 14,405 original constraints. These include exact cardinality 64, pair floors five, exact pair/triple counts, exact hole indicators, single-triple rows, softened two-triple rows, and four named core caps 55. There are no explicit hard quadruple rows. The 120 inherited soft-deficit variables retain domains 0 through 128 and their original rows, but have no objective weight.

Only the old objective and all hints are cleared, and only these two constraints are appended:

- At least 60 of the representative's 64 blocks must be selected.
- At most 11 triple-hole indicators may equal one.

The resulting model has 5,728 variables and 14,407 constraints. Standard protobuf comparison proves that removing the two appended rows recovers the frozen original after clearing its objective and hint. The parameter file changes only the random seed to `2026105201`; its budget remains 300 seconds with four workers. A separate outer process applies a 330-second watchdog and five-second termination grace. There is one child launch, at most one solver call, no restart, and no transfer of unused time.

For any two 64-element block families F and B, their replacement distance is `64 - |F intersection B|`. Thus overlap at least 60 is exactly the radius-at-most-four ball around this center. No selected incumbent block is individually fixed. Every family in that ball which satisfies the inherited constraints and the hole bound appears in this model, without requiring intermediate swaps to satisfy any rule. The added rows say nothing about families outside that local ball. This is not the unrestricted model and makes no global nonexistence or lower-bound claim.

Each of the four saved D29 ties is at replacement distance one from this representative. By the triangle inequality, every radius-three family around any saved tie lies in the representative's radius-four ball. This is only a containment statement; it imposes no candidate pool or assumption on how many changes a full cover needs. Because the inherited soft model lacks hard quadruple rows, its region must not be described as identical to the weak-pair scan's eligible region.

This is a feasibility model. CP-SAT may finish at its first family with at most 11 holes, even when that family is still a partial cover. The runner separately records `feasible_partial_found`, `feasibility_target_met`, and `cover_found`. Every callback and final feasible vector is saved, recounted, checked against every model row, and passed to both the package verifier and standalone verifier. The fresh metrics include actual D2max, D2sum, D3, D4, pair minimum, core overlaps, overlap with the center, and replacement distance. No old objective score is reused. A cover is claimed only when both verifiers confirm zero uncovered triples.

Finding a partial family meets only this pilot's target. `UNKNOWN` and timeouts are inconclusive. Even `INFEASIBLE` concerns only this bounded model and is not an independently checked theorem. Raw models, full vectors, logs, response data, and frozen source archives stay in ignored scratch; the manifest binds their exact bytes.
