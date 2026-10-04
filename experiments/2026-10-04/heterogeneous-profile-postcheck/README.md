```text
Document:    Independent Profile Pool Outcome Check
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      9d6f840773dc0ba769964c7362ae7c63f4c8f98ea13ee6f0b31d5b3d10b703a5
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Checked profile pool outcomes

Both 60-second, four-worker searches returned FEASIBLE with six uncovered triples, improving their eligible 17-hole hint. No covering witness was found. The raw best remains the earlier three-hole state, which contains a proved forbidden heavy-triple pattern.

The independent checker reads the saved models, parameters, responses and block lists without calling an optimizer. It checked 22 callback/final states, including final solver ties that differ from the callback witnesses. For every state it reconstructed all 4,948 variable values, checked domains and every active row, recounted the objective and inspected every set of five disjoint triples occurring at least six times. None of these 22 states has the proved five-heavy obstruction. All 44 package/standalone covering-verifier runs agree, and six damaged assignments were rejected.

The best callback and final states still retain 59 blocks of the original 60-block core. The elite final response has degree histogram 19:2, 20:12, 21:2; the expanded final response has 18:1, 19:1, 20:11, 21:3. Both final responses have triple histogram 0:6, 1:491, 2:58, 5:1, 7:4. Passing the named filters and the exhaustive obstruction scan does not establish that these partial states extend to a cover.

The outcome audit is `audit.json`, SHA256 `48c2cc037c18d496fd86906ba0418dc061773b73db817d6954dfe827401fa8de`. Each witness has paired verifier receipts under `verifiers/`. Final solver witnesses are saved separately in this folder. Frozen producer artifacts and the independent preparation gate remain unchanged; raw models, responses, parameters and logs remain in ignored scratch storage.

Run from the repository root: `uv run python experiments/2026-10-04/heterogeneous-profile-postcheck/check.py`. This is a partial-state audit, not a proof of a global bound or of nonexistence.
