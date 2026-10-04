```text
Document:    Independent H9 Neutral Queue Runtime Outcome
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      209d6ca9bd8641643d5d2a4fd7616641ca6a2e770ae2e0f8aad478d2af6e3947
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Checked H9 neutral-queue outcome

The sole H9 campaign processed eight centers and completed all 16 shell calls. It improved the stronger pair deficit from H9/D23 to H9/D21 at the first center and H9/D19 at the second. The hole count stayed at nine. The recorded queue then ended empty with `sample_exhausted`, zero pending frontier, and 42 combined historical/current visited hashes. No cover was found.

The best independently checked family has SHA256 `e2a00480dec1321be7a446e0969108c694420b225b054980470d3cdd53a1bb9c`, preserved as `family-e2a00480dec1321b.txt`. It contains 64 distinct blocks, has nine missing triples, minimum pair count five, D3=D4=0, D2max19 and D2sum25. Its old four named-core overlaps are [1,0,1,1]; the reported fifth-core overlap is one. It is three one-block exchanges from the starting family.

The audit reconstructed 21 distinct saved families across 42 references. Every family was recounted by direct subset inclusion and checked by both covering verifiers. All 33 observed neutral families were retained, no shell reached the 64-family cap, and the largest shell had eight neutral observations. Strict and neutral exchange identities, saved ordinals and full-ID order, exact shell counters and pruning accounting, normal completion, queue choices, old-history exclusions, budgets, and stopping labels agreed. No native query or optimizer was rerun.

The checker independently reconstructed the 34 prior center witnesses; every one is at one-swap distance 63 from the new start. The declared budget permits at most 16 centers, 15 transitions and a final two-swap inspection, hence inspected distance at most 32. It cannot reach those prior named centers. Starting fifth-core overlap one likewise yields a budget-dependent overlap bound of 33. The fifth core was only reported; the unchanged native kernels and independent legality oracle applied the old four caps. Among the saved families, the largest actual starting distance was five, the smallest historical distance was 63, and every fifth-core overlap was one.

The native shell semantics and prior independent audits support the completed finite-neighborhood claims. Unrecorded trial metrics were not re-enumerated. An uncapped retained queue ending empty is reported exactly as observed; this audit does not claim unrestricted infeasibility, general plateau exhaustion, or a global lower bound. No all-relabel escape or novelty conclusion is implied.

The producer result has SHA256 `2dc86eb41830d6647ad8dbc35b8211cb938a70f0f17c04bf68cd3042963c3811`. Independent `postcheck.json` has SHA256 `89142fc4522bf21bbf4c34dd06a855113474b54d73b6f793250d207d72ec47f6`. The independently reconstructed empty frontier has SHA256 `606fbe35bedfe52bb59c26c4ba98000df8b4f6ade458f58cf9cc535f666e7e8a`. The 47,137-byte tracked runtime receipt keeps concise family summaries; full verifier records are in ignored `experiments/scratch/weak-pair-h9-d23-neutral-queue-runtime-independent-20261004/families.json`, SHA256 `cf22de27e55d356c847d6e581b93cf3f2c62000f7e3268e34580209682ee65fc`.

The manifest is fixed at `64d63c5bee05e8ba8c5ca7bbb4f98b3258a6f3d6192297e792a4b62b12835d87`, and the pre-run GO gate at `98e162a80ba03d0ad532f10baf2e76e84d21fa5c7f5a659c97f79e58779f61fd`. The checker source SHA256 is `e502353d9f819e9dafebf6fd93ad99b261f0cc48b4897c951aff37a40efb34d6`. Source revisions, old native kernel/adapter bindings, raw runtime files, and historical source receipts remain pinned in the manifest and receipt.

The audit command was:

```sh
uv run python experiments/2026-10-04/weak-pair-h9-d23-neutral-queue-runtime-independent/check.py \
  --gate experiments/2026-10-04/weak-pair-h9-d23-neutral-queue-independent/gate.json \
  --gate-sha256 98e162a80ba03d0ad532f10baf2e76e84d21fa5c7f5a659c97f79e58779f61fd
```

The checker refuses to overwrite its existing receipt or detailed archive. All 21 independent canonical witness files are preserved in this directory.
