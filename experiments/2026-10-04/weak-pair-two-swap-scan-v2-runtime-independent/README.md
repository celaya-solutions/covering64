```
Document:    Independent Two-Swap V2 Runtime Outcome
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      ee84d0918d6761f17f9e69e067e5d970f258904b0b1f6a9efb22d7f9a97bc4df
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Checked runtime outcome

The sole v2 pass completed the exact-distance-two shell around the frozen
H12/D29 family. It accounted for all 18,668,272,896 distinct exchanges:
18,667,163,216 were safely pruned by pair-floor completion rules and 1,109,680
were evaluated. It reported 413,275 legal families and six strictly improving
neighbors, with one strict best record and six final ties at rank
(12 holes, 28 summed per-pair maximum stronger deficit). No cover was found.

The independent `postcheck.json` SHA256 is
`c2922a53aae7a51154b2006f457d88df886ab115fa6b88993920d04c62eb8d41`.
All six distinct saved families were reconstructed from their exchange IDs,
recounted by direct subset inclusion, and checked by the package verifier and
separate standalone verifier. Their hashes, complete metrics, missing triples,
and cover verdicts agree. There are no aliases between different exchange
identities. Each family meets the weak pair rules and named core caps; each has
full-row stronger deficit 28 as well as summed pair-maximum deficit 28.

The producer representative matches `swap-1142-1871-1154-3578.txt` exactly,
SHA256 `c6d132069270ead505488fa863a12a0f16a82e289c989a1c4d5961b13826e06f`.
The other five best exchanges and their full witnesses are preserved here.

The postcheck verifies the frozen pre-run gate, manifest, source and input
bindings, safe-pruning proof, production binary, archived sources, logs, terminal
counts, shell positions, strict record order, complete saved tie set, and CLI
verifier receipt. All 8,676,864 outer states completed, with no pending eligible
completions and a normal exit. The single 120-second budget was respected, with
no watchdog intervention, relaunch, or budget transfer. Native time was
4.21857 seconds and process wall time was 4.331355208065361 seconds; these are
observations, not a controlled benchmark.

Completeness is supported by the frozen audited loops, safe-pruning proof,
terminal accounting, normal exit, and unique exchange identities. This audit
did not independently recount unrecorded trials or run a second enumeration.
The result applies only to the pinned exact-distance-two shell under its named
legal filters; it excludes distances zero and one and proves no global lower
bound for C(16,5,3).
