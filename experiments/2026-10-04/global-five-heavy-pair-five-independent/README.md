```text
Document:    Independent Pair-Minimum DP Checks
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      8c8a688ea7efc5572692e2dd9228fc7f8d49f8cb44c95cbbcae2bbebf5ad6cbd
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent pair-minimum gate and outcome

The checker compares the full serialized parent model after removing exactly the 120 appended rows and restoring the parent hint. Every block remains free. Each appended pair row contains all 364 lexicographic carriers with lower bound five. The count follows from fourteen required triples through each pair and three covered per containing block.

The complete six-hole hint has objective 392, core overlaps [2,2,0], pair minimum five and global partition maximum 22. All 10,488 values satisfy the model; three damaged pair rows are rejected. The runner keeps the sole declared 120-second, four-worker budget and seed 2026104105.

The run returned FEASIBLE in 120.0117073750589 seconds. Two callbacks and the final response retain six holes. The objective improved from 392 to 391 by lowering original-core overlap from two to one. Independent postcheck verifies all model values, active rows, domains, thresholds, actual DP maxima, point/pair counts and both covering verifiers for all three records. Three damaged assignments are rejected. No cover was found and no infeasibility claim is made.

Replay from the research checkout with `uv run python experiments/2026-10-04/global-five-heavy-pair-five-independent/check.py` and `uv run python experiments/2026-10-04/global-five-heavy-pair-five-independent/postcheck.py`. Large frozen models and raw logs stay in ignored scratch; preparation and receipt hashes identify them.
