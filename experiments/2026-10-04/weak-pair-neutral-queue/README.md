```
Document:    Bounded Strict-First Neutral Queue
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      b9ff69229d6006382110948fd55352aa8d9a3f553043be8192a016374065952f
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Prepared neutral observation experiment

The checked strict-descent endpoint has H12/D2max=D2sum=26, pair counts `{5:80,6:40}`, zero D3/D4, and four named core overlaps `[1,1,1,1]`. Its canonical family hash is `f8d2525acd5dcb7db6e60bbff70b60612b12a0a6500bd25ac0841b4de18c955d`. Both complete strict shells found no improvement there, and the saved D26 bank contains only that already-scanned family. This new experiment records neutral observations that the old scans intentionally discarded.

The four evaluation/pruning headers are copied byte-for-byte. Each new native driver adds only an observer when a completed candidate is legal and its `(holes,D2max)` equals the round baseline. All old enumeration, pruning, metric evaluation, rollback, strict-improvement counters, strict-best ties, strict stdout, and budget checks remain in place. There is no new search kernel or assumption on legal intermediate swaps.

The observer counts neutral candidates and retains the first 64 in the existing deterministic traversal. Uniqueness follows from the existing one-swap and sorted two-swap exchange identities. The retained full-family block-ID lists are sorted before writing. They are a traversal sample, not the globally smallest 64 neutral neighbors. Reaching the retention cap does not end enumeration or skip strict-improvement checks. Separate files store the neutral sample and metadata; the existing strict recorder validates its original outputs unchanged before the adapter checks neutral counts, IDs, rank, metrics, uniqueness, order, and traversal positions.

The queue processes at most 16 centers and launches at most 32 shells, always one-swap then two-swap from the same center. Each shell retains its fixed 120-second budget, 135-second watchdog, and five-second termination grace. There is no retry, budget transfer, or automatic restart. The initial endpoint is the only historical-center revisit: its neutral output has never been recorded, and this new collector consumes center slot one. Every later center hash must be unseen among all pinned prior one/two-swap centers and this campaign's visited centers.

After two complete shells, strict improvement takes priority. Among all globally best strict ties from both shells, select the lexicographically least full sorted 64-element block-ID list. Clear queued families at the old, worse rank; retain unvisited tied siblings at the new rank. If there is no strict improvement, add the sampled equal-rank families to the deduplicated frontier and choose the lexicographically least full family. Queued families need not be adjacent to the immediately previous center, but every launched center has the current best rank and the same fixed weak/core legality.

Any incomplete or invalid shell stops the campaign without a next-center adoption or local-closure claim. A freshly dual-verified cover also stops it, even if a shell is incomplete; incomplete scope is retained. An early cover is an observed existence witness, not a completed-round optimum. Empty sampled frontier and the 16-center cap stop the run too. Empty improving output settles strict improvement only in that completed center's two shells; an exhausted capped queue does not prove neutral-plateau exhaustion, unrestricted nonexistence, or a global lower bound.

Every saved strict or retained neutral family is reconstructed, freshly recounted, checked against the fixed pair/single/quadruple/core rules, and passed to both verifiers. The inherited bounded executor preserves raw output on damaged terminals and never adopts from it. All logs, full candidate receipts, binary/source snapshots, and large records remain in ignored scratch. Compact center summaries and the exact center witnesses remain tracked and bind the full records by hash.

Preparation runs only synthetic queue controls, saved-output recorder replays, compiler builds, and a synthetic recorder-only native unit under address/undefined sanitizers. It does not execute either production search binary. Root alone may launch once an independent review binds the final manifest, starting family, runner, both new binary hashes, and their unchanged strict behavior.
