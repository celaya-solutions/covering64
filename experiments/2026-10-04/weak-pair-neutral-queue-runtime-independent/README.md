```
Document:    Independent Neutral Queue Runtime Outcome
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      656f02655db3881aec1ae1e3828ea144f2b84bd35a7eb80423b812d47caea7b9
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Checked neutral-queue outcome

The sole campaign processed 16 distinct centers and completed all 32 shell
calls. Its second center produced the first strict improvement, from H12/D26
to H11/D25. The remaining processed centers stayed at that best rank. The
campaign stopped at its declared center budget, not because the equal-rank
region was exhausted. No cover was found.

The independent `postcheck.json` SHA256 is
`fd044b1f88955403181b2d6ac739526c2d27ded14b0cff66f36a59d40a1cdde3`.
It binds producer result
`086524c3b7f8db6e11ab6b3e321c379facc36b3f51fb163740e7cc7fdac9d048`,
the combined pre-run gate, source revision, raw index, and every recorded
center and shell receipt. All 103 distinct saved families were reconstructed,
recounted by direct subset inclusion, and checked by both covering verifiers,
covering 469 references including the initial family. No search was rerun.

The best H11/D25 family has SHA256
`f621e945358cc9e51c53995ee9a4a6161a0124778984fa410a87227984a28a7a`.
It has 64 distinct blocks, pair floor five, zero single/quadruple deficits,
core overlaps [1,1,1,2], and full-row stronger deficit 25. Its complete canonical
witness is preserved here with the other checked families.

Every strict and neutral exchange identity, recorded ordinal, traversal order,
full-ID ordering, saved metric, canonical hash, and cover label was checked.
The audit independently replayed queue choices from saved observations: both
shells used the same center, strict improvements took precedence and cleared
the older frontier, and neutral choices respected full-ID lexicographic order
and the combined historical/processed exclusion set. All terminal counts,
pruning accounting, budgets, stopping labels, and summary links agreed.

The native logs report 488 legal equal-rank observations across the 32 shells;
456 were retained, with one shell hitting the 64-family sample cap. These are
counts of shell observations, not distinct global families. The sampling policy
retains the first 64 qualifying traversal families and sorts those retained
families by full IDs. It does not select the globally smallest 64 families.

`unscanned-frontier.json` has SHA256
`523ab6b38b23748885d19023d41b0dde5cdbd52b06b920aec6c1418f706ffe06`.
It contains 14 independently checked H11/D25 families in full-ID order: the
13 remaining queue entries plus the designated but unprocessed next center.
The set was independently checked against every observed final-best-rank
family after excluding all historically or newly processed centers. It includes
witness paths, IDs, metrics, dual receipts, and the combined visited hashes for
a separately scoped future campaign. Creating that receipt launched nothing.

Completed-shell claims rely on the previously audited kernels, observer-only
native delta, safe-pruning proof, terminal accounting, and normal exits.
Unrecorded trial metrics were not individually recomputed or re-enumerated.
The recorded samples and finite neighborhoods do not exhaust the equal-rank
region or settle unrestricted C(16,5,3) existence or a global lower bound.
