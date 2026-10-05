```text
Document:    Independent Replay of the Full New-Only Affine Support Screen
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      4becce57b66246d59fabde230653846ebcd527afb09a2b7234e198f883c730f6
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent replay of the full support screen

The gated v1.0.1 runner completed one pass over all 6,543,904 new-only pairs
in 543.84 seconds, inside its 650-second budget, with no watchdog action:

| Outcome | Cases |
|---|---:|
| Insufficient support | 5,352,656 |
| Immediate forced conflict | 983,774 |
| Survives one pass | 207,474 |

`check.py` replays every committed record without importing the producer. It
loads the frozen independent per-record checker from
`../circulant-chosen-link-support-runtime-independent/check.py` (SHA256 pinned),
which builds row carriers by the inverse construction, and supplies expanded
partials from the pinned packed catalog. It enumerates the new-only order
itself (fiber, partial, profile, skipping every mapped old partial) and
requires each record's ordinal to match. It checks the cases and survivor
streams against the cursor's committed byte lengths and hashes, the outcome
census, and that the survivor stream equals the survivors in the case stream.

All records pass in about 36 seconds with eight processes. The survivors are
then excluded by `../affine-lp-farkas/`. These are finite exclusions within the
stated recipe and branch, not a global result.
