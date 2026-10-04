```text
Document:    Raw H6 Reuse Pilot Independent Runtime Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      287bb87a3a13a0b216482c13e6b4cd79492f2561d5f096e99c53a1b018ab1e04
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Raw H6 reuse: independent runtime replay

The one authorized native run completed its 300-second budget without a cover. Native
return code was 1 (no cover); the enclosing Python runner returned 0 after saving its
successful validation receipt. No optimizer or native process was launched by this audit.

The initial raw family remained the raw and admissible best: 64 blocks, six uncovered
triples, minimum pair count 4, D2max 14, D2sum 498, D3 80 and D4 72. Its canonical hash
is `2d018ffa5e3e424193a4197b23891b52fa59b7ca411d06108e0ab1666bb85855`.
It is weak-ineligible, and its initial weak bucket was absent. The complete incumbent
is a separate verified 65-block Belic family; it is not an at-most-64 witness.

Four subsequent weak records appeared, all at 11 holes, improving D2max from 29 to 28,
27, then 26. The final weak family has minimum pair count 5, D3=D4=0, and six named
core overlaps `[0, 0, 0, 4, 1, 0]`. Its canonical hash is
`616b37190ee722bbd393821b4750d9279764deb992df4acf7a0c5a271d5b4344`.
This H11/D26 rank does not improve the previously checked H9/D19 family. The final
current state is a different partial family with 62 blocks and 38 holes.

The checker independently recounted seven distinct families at all 12 saved native
references and replayed 32 logged mutations. It checked both package and standalone
verifiers, all saved metrics, role ordering, strict record ranks, initial-role eligibility,
nullable weak fields, the complete65 fallback, five live caps, and saved-only sixth-cap
classification. Its 24 malformed trace controls were rejected. The original preparation
controls already cover absent weak, later first weak, and unconditional complete fallback;
this audit did not repeat native controls.

Native elapsed time was 300.001 seconds; wrapper elapsed time was 300.0120745829772
seconds. The watchdog did not fire and no restart or extra run occurred. Frozen manifest,
gate, wrapper, base driver, binary, inputs, sources, stdout and archive files were bound
by SHA256. The reported runtime return code is the native code, not the wrapper code.

The sixth cap only classifies saved exact64 files. It is null for non64 families. A later
six-cap-eligible live family can be omitted by unchanged strict five-cap buckets; this is
not a best-over-live result. The four weak hashes are absent from the selected finite
257-family comparison set (old205 inventory and three pinned prior runtime receipts);
this is not a complete historical or isomorphism novelty claim. No global exclusion,
nonexistence claim, or new all-relabel conclusion follows from this bounded search.

## Reproduce

The script only reads saved artifacts and refuses to overwrite its receipt. For another
replay, use a fresh sibling audit directory with the same source and frozen inputs.

```sh
uv run python experiments/2026-10-04/native-raw-h6-reuse-runtime-independent/postcheck.py --gate experiments/2026-10-04/native-raw-h6-reuse-independent/gate.json --result-sha256 8626d2045747ce3b630ac155ed0ee5b06de69b342b5bf645f1d17e63202cf4e2
```
