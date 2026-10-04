```text
Document:    Independent Radius Four Model Review
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      001ac8c492b6970b440ffef88238d3ba420b27e418fba5cbc4db15b12fd4a1a1
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Model-only review; no launch

The independent gate reconstructs the earlier frozen hole-priority model and compares the entire variable/constraint prefix, including all other protobuf fields. Exactly two new rows restrict overlap with the pinned H12/D29 family to at least60 and the exact hole flags to at most11. The objective and hint are absent. The parameter text differs only in the declared seed. All4368 block variables and the exact64-block equality remain unchanged.

Because two families each have64 distinct blocks, overlap at least60 is equivalent to at most4 replacements. The model covers only this local neighborhood. A feasible family with11 holes is partial progress, not a solution to the covering problem. A complete cover must pass both covering verifiers. A timeout or solver infeasibility status is not an independently checked global theorem.

The pinned family independently recounts asH12/D29. Its canonical5728-value vector passes all original rows and the new overlap row; only the11-hole bound fails. Separate row controls exercise all65 replacement distances and561 hole counts; these scalar controls are not covering witnesses. Three malformed family controls reject. The checker never calls a solver.

The v1 model-only gate is intentionally not an execution GO. Independent runner review found that a timeout during the child's JSON write could prevent a terminal record. The preserved v1 producer has not been launched; a new v2 sibling fixes that failure and requires its own gate.

Native OR-Tools proto getters may create empty optional messages: reading solution_hint or objective can change serialized bytes. This audit checks field presence before inspecting optional contents and uses lists before negative indexing.
