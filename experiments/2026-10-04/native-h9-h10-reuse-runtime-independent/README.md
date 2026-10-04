```
Document:    H9 H10 Reuse Pilot Independent Runtime Audit
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      582882c882d62106e15a4f2291743d9b22e3befa13b65c159536bab830506745
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# H9/H10 native reuse pilot independent runtime audit

The terminal audit passed. No complete cover of at most 64 blocks was found.
Both sequential 300-second runs completed normally, without a watchdog action,
restart, or budget transfer. The checker launched no optimizer or native search.
It recounted 10 distinct saved families and 28 saved references, replayed 32
trace mutations per run, and rejected 24 malformed trace controls.

| Seed | Saved raw/five-cap best | Saved weak best | Elapsed seconds |
| --- | --- | --- | --- |
| 2026105901 | H6, pair floor 4, D2max 14, D3 80, D4 72 | H9/D2max19, unchanged a0a737 | 300.007444 |
| 2026105902 | H8, pair floor 4, D2max 20, D3 156, D4 144 | H10/D2max22, unchanged 85f6 | 300.004981 |

The independently reconstructed sixth-cap report exactly matches the producer.
It contains only two distinct weak-qualified six-cap saved families: the two
starts. Both initial eligible fallbacks remain explicit. The best saved rank is
H9/D2max19; there is no new six-cap-qualified hash against the 250 distinct
pre-pilot saved hashes, and no improvement over the current starts.

The native recorder still applies five caps. The sixth cap was classified only
on saved exact-64 families. Non-64 records have a null sixth-cap verdict. Later
eligible live states can be omitted by the unchanged five-cap strict buckets;
this audit cannot establish the best six-cap state over the unsaved live walk.
D2sum is metadata, not ranking. The original driver result retains its historical
H11/D2max27 baseline; that comparison does not mean these starts are newly found.

The first raw H6 family has triple multiplicities {1:476, 2:70, 3:8}. The separate
`raw-h6-first-run-independent.json` recounts it with both verifiers and replays
the four old cores' five disjoint six-carrier heavy triples. At most three
candidate blocks can contain any triple. Therefore at least 5·(6−3)=15 blocks
are absent from every relabeling of each old 60-block core, giving overlap≤45.
This is stronger than a named-core check, but it does not make the family a
cover or repair its failed pair rules.

Across the three pinned pre-pilot inventories, the prior best raw family proved
by this old-core all-relabel heavy-support bound was H8; H6 improves that
particular checked class. The prior named-cap-passing raw minimum was H5, so H6
is not a new raw record under named caps alone. No all-relabel assertion is made
for the fifth or sixth core.

The checker binds manifest 13b26e00…, gate a8eb72f6…, wrapper b8e056e8…,
reused driver c0052cbf…, native binary 079eaf57…, both starts, and the independently
checked sixth-cap proof. Full hashes and file bindings are in `postcheck.json`.
The producer result is 59f4d29b…; the passing receipt is d3c7b5a6….

Reproduce in a fresh copy of this audit output directory, preserving the current
receipt (the checker refuses to overwrite it):

```sh
uv run python experiments/2026-10-04/native-h9-h10-reuse-runtime-independent/postcheck.py \
  --gate experiments/2026-10-04/native-h9-h10-reuse-independent/gate.json \
  --result-sha256 59f4d29bc851c1d56a4fa7b881d68643f7442fd0b6e0fab43e46668a97e570d9
```

`files-preparation.json` is the earlier preparation snapshot; its original README
bytes are preserved as `preparation-README.md`. `files.json` indexes the terminal
state. Neither finite search outcomes nor these local certificates prove
unrestricted infeasibility.
