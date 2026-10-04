```
Document:    Prepared Global Five-Heavy DP Full-Block Model
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      7828edbbe3441b379525d3bfb843f9af359b229f379d3f5dd9c4c4b4ad064840
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Prepared global five-heavy model

Preparation passed; optimization has not run. The full 4,368-block model retains the existing 4,958 variables, 1,188 rows, and objective as an identical prefix. It adds 1,120 exact global threshold Booleans, 2,240 channeling rows, 4,410 reachable DP variables, and 99,917 recurrence rows. The result has 10,488 variables and 103,345 rows. All three audited core caps remain at 55, and the three named profile filters remain as redundant prefix rows. The objective stays 65 times holes plus original-core overlap.

The checked ten-hole hint has core overlaps [1,8,55], objective 651, and global partition maximum 24. Its complete 10,488-value hint assigns every DP variable its least recurrence value. Every domain and active constraint was recounted. No incumbent incidence, heavy-set, graph-family, or point-symmetry restriction is added.

The frozen model is `experiments/scratch/global-five-heavy-dp-20261004/full-4368-model.pbtxt`, SHA256 `ee2570107d996ee8f69a0118b11abbad91320f5b19eb6e196ef6a34367d5d295`. It is 28,669,992 bytes and stays under ignored scratch. The manifest SHA256 is `d01230c07cb5b1226d2fcc95912586ac5ff07723da4e170be5e908167eeb9f5b`; source SHA256 is `477e8e03630185c233bbd61e8a12d9b4361cb45e271ad4bdfecdf875a635e24e`. Source snapshots, DAG tables, input hashes, full hint provenance, and parameters are bound by the preparation evidence.

Building took 0.357088 seconds, validation and complete hint recount 9.906872 seconds, and serialization 0.088189 seconds. Peak process memory was 286,015,488 bytes, including imports, model, checking, and serialization. These are build-only measurements and do not predict search speed.

The saved parameters describe one future run: 120 seconds, four workers, seed 2026104104. A separate independent gate is required before that run. The producer has no optimization entry point. The failed initial attempt used an unavailable parser helper and stopped before model creation; its source and log were preserved under ignored development scratch before the direct block parser repair.

The five-heavy theorem is a necessary condition for full covers. It may exclude some near-cover families while retaining every valid 64-block cover. No new covering witness, unrestricted infeasibility result, or global lower-bound theorem is claimed by this preparation.
