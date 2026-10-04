```
Document:    Independent Bounded Descent Runtime Outcome
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      66ff1df948c908e286c893c05096b3beda4f93ca58c8fa7d820d6ba7f6f1ac6d
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Checked bounded descent

The sole campaign completed three rounds and six shell calls. Starting at
H12/D28, it adopted H12/D27 after round one and H12/D26 after round two.
Both round-three shells completed without a strict rank improvement, so the
campaign stopped with `no_strict_improvement`. No cover was found.

The independent `postcheck.json` SHA256 is
`13e39d802c2e7433d3f983e027e07c53edc866364f9fe8cc8088a3f92a937765`.
It binds the frozen gate, manifest, runner, original source revision, logs,
per-shell receipts, budgets, candidate audits, and all saved families. Seven
distinct families were reconstructed, recounted by direct subset inclusion,
and checked by both the package and separate standalone verifier. Their
metrics, missing triples, canonical hashes, and covering labels agree.

Both shells used the same fixed center in every round. The independent audit
recomputed all recorded exchange ordinals and final accounting, checked the
complete saved best-tie sets, and independently selected the least full sorted
ID tuple among the best strict-rank families in each round. Both adopted
centers match. Each saved candidate and center receipt matches its witness.

The final center has 64 distinct blocks, 12 holes, summed pair-maximum deficit
26, full-row deficit 26, pair floor five, zero single/quadruple deficits, and
core overlaps [1,1,1,1]. Its SHA256 is
`f8d2525acd5dcb7db6e60bbff70b60612b12a0a6500bd25ac0841b4de18c955d`.
Its independent witness is preserved among this folder's seven family files.

All six shell calls respected their separate 120-second native budgets, with
no watchdog intervention, relaunch, budget transfer, or extra shell directory.
The six recorded process times sum to 13.931079
seconds; this is an observation, not a controlled speed benchmark. The audit
launched no search and did not independently recount unrecorded trials.

The final closure claim means only that neither a one-block nor an exact
two-block exchange strictly improves the (holes, summed pair-maximum deficit)
rank under the fixed named weak rows and core caps at this exact D26 center.
Equal-rank moves, longer paths, other centers, and unrestricted C(16,5,3)
existence remain open. Four-round exhaustion would not imply this closure;
here the campaign stopped earlier after two completed nonimproving shells.
