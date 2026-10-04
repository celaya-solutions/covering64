```text
Document:    Independent Native Fourteen Cut Runtime Review
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      0fb7d85fb79193d32343ebc6bbdf73f4e8456f201b24856fc1c8b20410c48fef
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent native multicut review

`check.py` recounts all 286 saved states and replays all 88 saved moves and
rollbacks from the v1.4.0 control campaign. It recomputes all 14 heavy cut sums,
the maximum positive violation, ceiling division, weights 1/10/1000, base
coverage and pair scores, and the full score. It reuses the pinned earlier
independent lookahead oracle for that unchanged term. Ten distinct states were
present; disabled-guide controls match the original binary's block lists.
The source review confirmed heavy-template delta updates, ordinary-move
preservation, rollback restoration, and the zero-hole acceptance override.

`supplement.py` binds v1.4.1. Its only body changes are three terminal-state saves
for normal completion and the two immediate-cover exits. All 286 new witness
and detail files match the independently recounted old controls byte for byte.
All 88 operation traces match after directory normalization. The supplemental
gate binds the new optimized binary and source hashes. Native standard error
was empty and scoped Ruff passed. The primary campaign separately checked the
optimized and sanitizer builds and embedded catalog sums.

These reviewers ran no optimization. The cut guide is a score in the restricted
regular four-sevenfold search; it adds no block-pool restriction and gives no
unrestricted exclusion. Full runtime receipts are `audit.json` and
`audit-v1.4.1.json`; source and binary binding must follow the matching version.
