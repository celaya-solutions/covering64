```text
Document:    Strong Core-Cap Matched Release Pilot Outcome
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      ed0ea109eab69fdbda8a4c6b2395ff61c57f2dbc2dcac08cf9f61e6c1852b3ca
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Result

The adaptive 952-block case ended with 13 uncovered triples. The full 4,368-block
case ended with three, but its last eight saved/final records have a proved
five-heavy obstruction under a newly observed point partition. The three-hole
state is therefore not an eligible improvement toward a 64-block cover.
No complete cover was found, and no global lower-bound claim follows.

| Case | Status | Wall seconds | Final holes | Original-core overlap | Composite |
| --- | --- | ---: | ---: | ---: | ---: |
| adaptive-952 | FEASIBLE | 120.00826274999417 | 13 | 1 | 846 |
| full-4368 | FEASIBLE | 120.00884000002407 | 3 | 1 | 196 |

Both objective bounds were zero. Each case ran once with seed 2026104102,
four workers, a 120-second solver budget and OR-Tools 9.15.6755.
The objective was `65 * holes + original_core_overlap`.

# Essential correction

The earlier matched pilot retained 59 blocks of a known 60-block core. An older,
independently replayed certificate already proves that any full 64-block cover
can retain at most **55** blocks of that core, under any point relabeling. The
old six-hole states remain valid recorded partial covers, but violate this
necessary condition for full covers. Earlier frozen sources and results remain
intact.

The standalone certificate checker replayed all 8,337 orbit representatives,
covering all 487,635 four-block removal sets. Its smallest exact dual bound was
2,035,711/250,000, greater than the eight allowed additions. The separate
`../core-cap-independent/` audit checked the original and mapped core images
against all 4,368 blocks, 560 triples and 43,680 block-triple incidences, and
rejected seven damaged-certificate controls. This transports the existing cap
55 to the two rows used here. Cap 54 is not established.

# Frozen comparison

The adaptive 952-block pool and full 4,368-block universe were unchanged from
the earlier matched comparison. Both models replaced their two core-at-most-59
rows with core-at-most-55 rows, retained both proved five-heavy partition cuts,
and released all 64 selected slots. Each model had 4,948 variables and 1,166
rows. There was no radius or added overlap cap.

`hint-selection.json` recounts 36 already checked saved paths: ten original
inventory seeds, the profile-pool checked states, and the earlier matched-release
saved/final records. Ten passed the two named cap-55 rows and profile cuts.
Ordering by holes, original-core overlap and path selected
`../heterogeneous-profile-pool/elite/best-02-h14.txt`. It has 14 holes,
original/mapped core overlaps 1 and 7, and composite objective 911. Its canonical
SHA256 is `e942f6018640e2ead11e6e1f4ec9c3d16cf64166ed504f680f2fd04207cd0e2c`.
This eligibility check concerns the declared cuts, not all possible relabelings.

The complete models, parameters, responses and logs are hash-bound under
`experiments/scratch/six-hole-strong-core-release-20261004/`. The independent
gate passed before the two optimizer calls. No additional solve or adaptive
partition separation occurred within this frozen pilot.

# Trajectories

The saved adaptive objectives were `911 -> 846`, with holes `14 -> 13`.
The saved full objectives were
`911, 781, 716, 651, 521, 456, 391, 326, 325, 197, 196`, with holes
`14, 12, 11, 10, 8, 7, 6, 5, 5, 3, 3`.
Native final responses chose different tied families from the last callback
snapshots: 59 common blocks for the adaptive case and 60 for the full case.
Each final response was saved and verified separately.

# Independent postcheck

`../six-hole-strong-core-release-independent/postcheck.json` passed the audit of
15 saved/final records, representing 14 distinct families. Both the package
verifier and standalone `scripts/check_cover.py` checked each record. The audit
also checked complete native response assignments and rejected seven damaged
response controls plus malformed-label, duplicate-block and damaged-cardinality
witness controls. The audit made no optimizer calls.

Eight full-universe records, beginning at the saved eight-hole state, have the
same forbidden partition:

`(1,2,3), (5,6,7), (8,12,16), (9,10,11), (13,14,15)`.

The final triple multiplicities on this partition are `7,7,7,7,6`. These violate
the already proved five-heavy rule. Neither of the two profile rows frozen in
this pilot represented this new partition. The final histogram over all 560
triples is `0:3, 1:499, 2:52, 3:1, 6:1, 7:4`.

The adaptive final has no five-heavy violation found by the exhaustive profile
scan. The supplementary relabeled-core screen found a necessary partition but
no explicit violation among its 242 checked core images. That limited screen is
inconclusive about all point relabelings; it does not certify global cap-55
eligibility. A necessary partition alone is not an explicit core transport.

# Supplemental exact core transport

The later solver-free audit `../third-core-independent/audit.json` independently
verified the heuristic transport with point images
`[16,15,12,5,11,8,4,7,3,6,1,2,10,14,13,9]`. It checked all 16 labels,
4,368 blocks, 560 triples and 43,680 incidences. The full final state retains
60 blocks of this transported core, exceeding its checked bound of 55. This
supplies a second explicit obstruction to the final three-hole state.

For this third core, the full saved trajectory overlaps are
`51,52,53,55,55,57,58,59,59,60,60`; the final native response also has overlap 60.
The adaptive saved states have overlap 51, and its native final response has
52. This third core was not a frozen row in the pilot. Its bound may be used in
a separately frozen continuation together with the new five-heavy partition,
while retaining every existing cut. No rerun is part of this report.

Supplemental audit SHA256:
`6a3881254e8c659459174bb79630c2b78d946d35f40f52ca472149410820deb9`.

# Integrity and scope

- Frozen runner SHA256: `a570ebded365c26ffcc90ece8c3c27f72e182b4df5bb2ab46b813fa087738ebf`.
- Frozen manifest SHA256: `7b7266c9ed7a6c57a0959afd9b396af40aa3e89b5155efac8e26c006aa8f274d`.
- Result SHA256: `10c4dfe56d9ccbe871d6bd97f63b090a4a5b506e9d8d5c3f143ed59ad36f5c9a`.
- Independent gate SHA256: `8f10401247ab59c83925088a63e093725d51bbed8b81312b7c5b9d902813397d`.
- Independent postcheck SHA256: `a2af3ec3400bcf2102941e6de69e53f253549717fbd0112a455b5d1be85a5741`.

The complete file index in `files.json` covers this report, frozen inputs,
result and all saved witnesses. The gate and manifest record the exact model and parameter hashes.

This bounded comparison is a construction experiment. FEASIBLE with holes is
not a cover, zero bounds do not prove optimality, and timeouts or UNKNOWN are
inconclusive. The named profile and core cuts are necessary conditions for
64-block full covers. Finding another relabeled forbidden basin does not prove
that a 64-block cover is impossible.
