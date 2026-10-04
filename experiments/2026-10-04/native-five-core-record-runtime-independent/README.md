```text
Document:    Independent Five-Core Native Campaign Runtime Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      c874f53b0035b473890372f4d23b6882144ef097269d81351ae9a544061e9f90
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Checked two-start native campaign

Both declared native runs completed normally, sequentially, with no watchdog, relaunch, or cover. The final producer result has SHA256 `5c11a6ee25247bc7b3caf707ae05aba8387d2c5c5a8e26642a483397b451c8f3`. The independent full-campaign receipt is `postcheck.json`, SHA256 `5d79cdfc0820086e14281538398506c674ce9ecb241e1b3b3739b7aabb067862`.

The best weak-qualified family improved from the historical H11/D27 baseline to H9/D23. Its SHA256 is `f5f24d57738763380c715769eef4328d7f1950a8ae6d0eedd8e9ff16dc3fc681`, saved at `../native-five-core-record-pilot/seed-2026105601/search-final-weak64.txt`. Fresh direct inclusion counts and both covering verifiers agree on 64 distinct blocks and nine missing triples. Its pair minimum is five, D3 and D4 are zero, D2max is 23, D2sum is 29, and the five named-core overlaps are [1,0,1,1,1]. This is improvement among the checked qualified families, not a cover or a novelty claim beyond the frozen finite inventory.

The second start retained a weak-qualified H10/D22 family, SHA256 `85f6e38a537691442cf6097a68b1364a755ac1ba8312d61adfc88c26abb6a90e`. It has pair minimum five, D3=D4=0, D2sum32, and five overlaps [0,2,1,2,1]. Its raw best has eight holes and passes the five caps, but fails the weak rules: pair minimum four, D3=52, D4=48. Raw, cap-admissible, weak-qualified, and complete records remain separate. The initial 65-block complete incumbent is never treated as an exact-64 candidate.

The audit freshly reconstructed and dual-checked 27 distinct families across 43 saved references. Nine qualified family hashes are absent from the frozen historical inventory, and six checked qualified families improve its H11/D27 rank. These are literal hash comparisons; no isomorphism or all-relabel novelty conclusion follows. All stored IDs, metrics, weak profiles, caps, historical comparisons, initial record roles, strict bucket ranks, final bucket identities, and witness-file membership were independently checked.

The first 32 logged mutations of each run were replayed against direct triple counts, for 64 replayed mutations total. Twenty-four malformed trace controls were rejected using the pinned prior checker. Unlogged search decisions were not re-enumerated, so the audit does not prove trajectory exhaustiveness.

The manifest fixes two sequential 300-second runs, seeds 2026105601 and 2026105602, a 315-second watchdog, five-second termination grace, and no restart or budget reallocation. Observed process durations were 300.305664292071 and 300.00519079202786 seconds. Both exits were normal and unsuccessful; run timestamps confirm sequential execution. Manifest, combined gate, binary, dependencies, old raw inputs, frozen source archive, run logs, and final witness hashes all agree.

The manifest SHA256 is `32d536037298694fea21fa8207efb328851d9ede135cae2c770833863891ee86`; combined GO gate SHA256 is `10477409a380ff6fc6a912b6349c7e8e418dcc8b3afab84fe3fab0f5f8eb0e59`; checker source SHA256 is `718e311fe6e1ef50e23d2be7f03e5e6b608b1969fbf926f7f7b1742254937884`. The independent oracle, prior helper, package verifier, standalone verifier, and historical inventory are also bound in the receipt.

The earlier first-run receipt is preserved as `partial-postcheck-seed5601.json`, explicitly marked incomplete. Its producer bytes are retained in `partial-producer-result-seed5601.json`; the live producer result was later extended to include the second run. `seed-2026105601-weak-final.json` preserves the independent early H9 confirmation. The earlier agent's `provisional-weak-records.json` remains unchanged. The full receipt supersedes those progress observations.

The completed audit command was:

```sh
uv run python experiments/2026-10-04/native-five-core-record-runtime-independent/postcheck.py \
  --gate experiments/scratch/native-five-core-record-pilot-20261004/frozen-sources/gate.json \
  --result-sha256 5c11a6ee25247bc7b3caf707ae05aba8387d2c5c5a8e26642a483397b451c8f3
```

The checker refuses to overwrite an existing receipt. No native query or optimizer was launched by this audit. These bounded heuristic outcomes do not settle unrestricted C(16,5,3) existence or establish a global lower bound.
