```text
Document:    Native Variable Cardinality Pilot Outcome
Version:     v1.0.1
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      14b0e2bc835d9a9758614b751fdeea0962c9ea786642bd016a8176a40afdd70d
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Outcome

Neither approved 120-second call found a complete family of size at most 64.
The two calls ran sequentially, with no relaunch or budget transfer. The root
agent collected terminal campaign process exit 0. Both native calls returned 1,
finished normally, passed all saved-family checks, and left empty stderr.
Neither watchdog fired. This is a heuristic failure, not a lower-bound proof.

| Seed | Iterations | Native seconds | Process wall seconds | Best raw exact64 holes | Best four-cap admissible exact64 holes | Actual final size / holes |
|---|---:|---:|---:|---:|---:|---|
| 2026104701 | 17,000,124 | 120.001 | 120.295269 | 3 | 13 | 64 / 20 |
| 2026104702 | 15,910,807 | 120.001 | 120.004188 | 3 | 12 | 64 / 26 |

The best complete cover remained the pinned Belic 65 in both runs. Both walks
visited sizes 62 through 64 after their initial 65 state. The driver recorded
25,242,207 and 23,622,169 block mutations. Three incoming choices per call used
the explicit fallback; their recorded novelty counts were 1,871,844 and
1,749,955. No source bytes or manifest-bound input changed during the campaign.

The raw exact64 incumbent was identical in both calls:
`d6dcfd2f1778f76c90ca67698865f683a44a6b69ddacad8f77cc4ee9021eacdf`.
It was created by the initial removal of lexicographic block ID 2236 and retains
all 60 blocks of the old core. Its three holes therefore do not qualify for the
admissible record. Raw and admissible families remain distinct artifacts.

The final admissible records are:

- Seed 2026104701: 13 holes, four overlaps `[55,0,1,1]`, SHA256
  `07a47325098b1e562f9c46b4eac426a05c4ca19b8f3f2e2c7e69c0afcf296468`.
- Seed 2026104702: 12 holes, four overlaps `[1,1,1,2]`, SHA256
  `330788e4a6f24e1852b047f5cd2447bfa83da66ea8c6daba3287eb53088c4b00`.

The seed 4701 admissible record reached 13 holes at step 60, about 0.000855 seconds,
and never improved afterwards. Seed 4702 reached 12 holes at step 3,574,271, about
27.943 seconds. Final overlaps were `[0,1,0,1]` and `[0,1,1,2]`: both walks escaped
the named old core. These observations do not prove that initialization caused
failure or that either trajectory was trapped. The independent post-run screen of the unique best admissible family (H12)
found zero necessary old-core partitions. It therefore certifies old-core
overlap at most 55 under every relabeling. This result is stronger than the
four named caps and is saved in `native-variable-cardinality-relabel-screen`.
Its screen SHA256 is
`159ca06adb57ed636e52d19da8d42c36a35d26a56827bfcd840f8c2b91bc3e98`;
its independent manifest SHA256 is
`50b83a48399e2f3f6458181987eeee94e4d847c1b5d13a31aa0f7a598d26870e`.

# Checks and receipts

The prelaunch independent gate passed 213 naive state snapshots, 930,384 block
score checks, 500 incoming-selection checks, 11 API rejection controls, all four
reached move branches, and AddressSanitizer plus UndefinedBehaviorSanitizer.
Its gate SHA256 is
`300677f074664d001cba3c63cb156e13e2648020cfa28908560b5f761ad3c6ff`.
The frozen manifest SHA256 is
`f79075467ba41b46e53491c032044a23fe9766c680309055c1ff5d0697ec354b`.

The runner verified 8 and 11 saved families, respectively, including record and
final copies. Every family passed structural checks and was checked by both
the package verifier and standalone checker with its actual block count.
Partial families correctly returned incomplete; the retained 65-family was
complete. Producer wrap-up rechecked every saved-family hash and stdout hash,
confirmed both final log events match result metadata, and found empty stderr.

Final result SHA256:
`43e1f4edff6abe1f28db92c07594083d4c765850ed3c944a7ac42962b7c467ab`.
See `outcome-files.json` for supplemental hashes and raw-log receipts. The original
README, source, controls, inputs, binary, and manifest remain unchanged.
