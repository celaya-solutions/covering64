```text
Document:    Independent Third Core Transport Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      8d1b65e8cf90d192a815e4f8a21edd7346e7c3b0f261f14a1e37a3a53cbe5e05
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# A third exact core image

The explicit point map in the transport witness was checked independently:

```text
point:  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16
image: 16 15 12  5 11  8  4  7  3  6  1  2 10 14 13  9
```

It maps the saved 60-block core to exactly the 60 distinct block IDs in
`audit.json`. All 60 occur in the three-hole full-universe final family from
the strong-core pilot. The map and its inverse were checked against the core,
all 4,368 blocks, all 560 triples, and all 43,680 block-triple incidences.

The independently replayed four-removal certificate therefore transports to
this core image. The warranted additional row is the sum of these 60 block
variables at most 55. The source family has overlap 60 and violates that row.
All 15 already doubly verified pilot records were recounted against this same
core image; their exact overlaps are saved in the audit.

Five damaged controls were rejected: a nonpermutation, a changed map, a wrong
core ID, a wrong overlap, and an unsupported upper bound of 54. This audit checks
the explicit witness directly and does not rely on completeness of the sibling
map search. No optimizer was called, no cover was found, and no global
nonexistence result is claimed.
