```text
Document:    Frozen G1 Finite-Screen Source and Certificate Archive
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      74f2559d31a30c5b26a0fdce7c1222c476a4e3ef5a09ecbe372a11161aac44b5
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```
# Durable finite-screen archive

`count.py` and `envelopes.py` are unchanged byte-for-byte copies of the executed
sources from `experiments/scratch/g1-next-route-plan-20261004/`. `archive.json`
binds the original and tracked paths, hashes, compressed sizes and restoration
format. The compact receipts and source inventories are retained beside them.
No original frozen source or audit input was changed to make this archive.

The finite enumeration found 580 registry-safe proper three-edge replacements,
5,541 paired two-anchor replacements, 100,076 whole-link replacements and 595
unique neighbors of the top five saved alternatives. The first 243 g1 planes
exclude every state in the three-edge, paired and saved-alternative pools.
Combined with the 353 broad planes, they leave 757 whole-link states at envelope
zero. A zero lower envelope is inconclusive, not a fractional feasible point.
The independent audit is in `../g1-larger-independent/`.

`g1-cuts.compact.json.gz` preserves the 243 signed-row certificates. The sibling
whole-link-certificate folder preserves the later 1,000-plane compact bundle.
Coefficient arrays omitted by this compact format are integer sums of saved
signed rows; `restore_bundle.py` restores the exact original JSON bytes and
checks the expected SHA256 before optionally writing them. Run the restoration
script with an archive path alone for a read-only validation, or use `--output`
with a new path to materialize the original bytes. Both archives passed this
exact restoration check. The broad-reference gzip is ordinary gzip of the
unchanged frozen 353-plane JSON.

To repeat enumeration and algebraic screening, copy the unchanged `count.py`
and `envelopes.py` into a fresh sibling of their original ignored planning
folder, retain the repository layout, restore the input artifacts listed in
`inputs.json`, and run `count.py` followed by `envelopes.py` with `uv run python`.
The scripts perform zero optimizer calls. Output timestamps and new artifact
paths can differ; candidate tuple hashes, row arithmetic and score arrays are
the scientific replay targets. Run budgets belong only to the separate gated
LP experiments, not to these finite arithmetic passes.
