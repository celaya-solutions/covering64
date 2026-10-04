```text
Document:    Independent Global Five Heavy Filter Proof and Outcome
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      f52fee335ac0a6806b7c1527e8872d9884d18f2e2d46332075e967849d6c9cd5
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Checked global five-heavy filter

The proof audit independently reconstructed the full recurrence and its reachable subset, checked both directions of the trimming argument, all 4,410 constructive paths, threshold truth tables, small direct partitions and the existing unrestricted five-heavy theorem. The trimmed recurrence has 4,410 auxiliary states and 99,917 rows. Existence of bounded DP values is equivalent to excluding every five-disjoint-heavy pattern, although arbitrary feasible DP values need not equal their minimum possible values.

The separate model gate checked every variable, domain, new row, objective, complete hint and frozen parameter. The previous 4,958 variables and 1,188 rows remain unchanged; 560 pairs of exact threshold indicators and the trimmed recurrence bring the model to 10,488 variables and 103,345 rows. Three damaged recurrence controls were rejected. No point regularity or incumbent incidence pattern is imposed.

The sole declared 120-second, four-worker run returned FEASIBLE with objective 651 and ten holes. The saved callback and native final response both retain exactly the initial block family, with core overlaps [1,8,55] and maximum partition weight 24. Postcheck validated every active row and auxiliary value, independently reconstructed the actual maximum, ran both covering verifiers on both records, and rejected three damaged assignments. DP response values were allowed to exceed their least feasible values. No covering witness was found.

The state has minimum point degree 19 and minimum pair count 4, with three pairs below the necessary full-cover count of five. These are diagnostics only; no new pair rows were added to this run. Preparation and outcome hashes are in `proof.json`, `gate.json`, `postcheck.json` and the producer's `outcome-files.json`. Large serialized models and full response vectors remain in ignored scratch storage.
