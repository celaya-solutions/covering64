```text
Document:    Exact Fixed-g1 Whole-Link Exclusion Certificates
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      7fbb46324f95ec5b0729ce69c54e417b324747993bad31c0f73a914c27ab98f7
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```
# Saved-dual certificate replay

`extract.py` performs no optimization. It binds the independently checked 757
whole-link LP records, recreates their exact shifted g1 rows, rounds the saved
signed duals at denominator one million, and verifies positive integer gaps.
Every signed row weight has absolute value at most its denominator, so the
same planes also give valid lower bounds on the elastic objective.

The **757 new positive certificates** join the prior 243 g1 planes, for
**1,000 graph-specific planes**. They remain separate from the 353 broad planes.
The smallest new exact source gap is **165832/15625 = 10.613248**, at rank 648.
The corresponding numerical objective was 10.613462674257228.

The independent audit in `../g1-whole-link-certificates-independent/` replayed
all 1,000 integer row combinations and rejected four malformed/damaged controls.
It verified that the 757 new source tuples are exactly the zero-envelope
complement of the prior finite screen. Thus 99,319 earlier positive envelopes
plus these 757 positive source certificates exclude fractional completion for
all **100,076 registry-safe whole-link replacements** in the declared fixed-g1
neighborhood. Registry-excluded link replacements are handled by the earlier audited
first-link proofs. This is a finite neighborhood result, not an elastic optimum or a
global covering-number lower bound.

The raw 1,000-plane bundle remains at the path in `result.json`. The tracked
`all-g1-cuts.compact.json.gz` retains every signed-row certificate and metadata,
with derivable heavy and ordinary coefficient arrays replaced by markers.
`../g1-larger-source/restore_bundle.py` reconstructs the original frozen JSON
bytes and checks their SHA256. Exact restoration was tested. Large numerical
vectors and raw model artifacts remain ignored; no frozen audit input changed.
