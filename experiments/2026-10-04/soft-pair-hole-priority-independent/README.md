```text
Document:    Independent Hole-Priority Soft-Pair Gate
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      cd98525802e65359637ea1fd9b742943b20466e4a4a8e8a67c4c9f9e6e6226a5
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent preparation gate

Every proto field except the complete hint and objective matches the previously checked H12 soft model. The new objective is exactly 15,361 times the 560 hole flags plus the 120 deficit auxiliaries. Each deficit domain is [0,128], so their total is at most 15,360: eliminating one hole strictly outweighs any possible deficit difference. The complete independently recounted H12/D2=32 hint has objective 184,364 and satisfies all 14,405 rows and 5,728 domains. A decreased required deficit fails; legal auxiliary slack passes.

Parameters change only from seed 2026104901 to 2026105001; the 300-second and four-worker limits remain exact. Frozen source, prior checker/runner, proof, input, model, parameter and hint hashes are checked.

Root reviewed the complete runner diff. Objective evaluation uses the new weights. A separate pure classification function requires both covering-verifier verdicts to match the actual hole count, and keeps positive-hole zero-deficit hints distinct from covering witnesses. Independent scalar controls confirm that such hints do not stop search, mismatched verifier verdicts fail, and the sole stop_search call is guarded by covering. These scalar positive controls are synthetic policy tests, not covering witnesses. All full vectors and callback/final records remain captured.

One root-owned run is allowed by this gate. A timeout or failed construction does not prove nonexistence. No optimizer is called by the checker.
