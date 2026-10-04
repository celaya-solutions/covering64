```
Document:    Variable-Cardinality Best-64 Relabeled-Core Screen
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      cf918d4a4f12ede97b197092bf2df9ee3996d5c80f633c7a6ef60838559a9250
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Best admissible 64-block relabel screen

The two-seed native variable-cardinality pilot finished without a complete family of at most 64 blocks. Its final admissible 64-block records have 13 and 12 uncovered triples. This check selected the minimum, retained distinct tied final families, and found one unique candidate: seed `2026104702`, with 12 uncovered triples and named-core overlaps `[1, 1, 1, 2]`.

Both the package verifier and separate `scripts/check_cover.py` confirm 64 distinct, lexicographically ordered blocks and the same 12 uncovered triples. The candidate SHA256 is `330788e4a6f24e1852b047f5cd2447bfa83da66ea8c6daba3287eb53088c4b00`.

The frozen relabel helper found **zero necessary partitions**. Therefore this candidate shares at most 55 blocks with every point relabeling of the original 60-block core. The original core contains five disjoint triples, each in six core blocks. An overlap of at least 56 would omit at most four core blocks; a five-point block contains at most one of those disjoint triples. Such an overlap therefore requires a five-triple partition with total incidence deficit at most four. Exhausting that necessary condition returned no partition.

The 242 explicitly tested images had maximum overlap 4. That finite-image maximum is not a global maximum; the all-relabel cap follows from the empty necessary-partition set. The helper's pruned-versus-exhaustive controls, positive core control, and zero-incidence negative control passed.

`screen.json` binds the terminal producer result, manifest, archived gate, source/input/raw hashes, helper hash, selected family, and both verifier receipts. The check made zero optimizer calls. It applies only to the selected saved 64-block family, not to the 65-block start or other variable-cardinality states. This family is a noncover; the result supplies no global existence or lower-bound conclusion for C(16,5,3).

Reproduction command: `uv run python experiments/2026-10-04/native-variable-cardinality-relabel-screen/check.py`. The checker refuses to overwrite the completed screen; reproduce in a fresh audit directory with the same bound inputs.
