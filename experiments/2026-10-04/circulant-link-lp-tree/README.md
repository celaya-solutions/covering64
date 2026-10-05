```text
Document:    LP-Certified Branching over Circulant Excess Profiles
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      be5a019cd0a6056b5020138e155a2eeb338d31aae194737ff7d5e05f02d64e43
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# LP-certified exact-cover tree: pilot on one profile

## Idea

The bounded LP rejected every fixed affine link instantly, and greedy LP dives
on whole circulant profiles failed after fixing only five or six point-one
blocks. `tree.py` turns that into an exhaustive search for one profile of the
circulant `{+-1,+-3,8}` branch. With the profile, every triple has exact
multiplicity one or two and a cover is a 0/1 vector over all 4,368 blocks.

The tree branches on the open triple row with the fewest candidate blocks
(ties prefer rows through point one). Child i fixes candidate i to one and
earlier candidates to zero, so the children partition the node's solutions
by first selected candidate. A node closes by a support deficit or by an
integer Farkas vector with positive exact margin over its residual rows and
open blocks; GLOP only proposes the vector. A node meeting every demand would
be a cover candidate for both checkers.

## Pilot

Profile 0 ran for its 1,500-second budget (`pilot-profile-0-result.json`):
2,922 nodes, 2,614 Farkas leaves, 93 support leaves and 2,829 LP calls; 128
nodes stayed open. The root row (1,2,3) has 78 candidates; only its first two
subtrees finished (1,424 and 1,219 nodes) and the third was in progress. A
24-entry certificate cache never matched a sibling. About half a second per LP
call puts one profile near ten CPU hours, so the 52 profile orbits would need
hundreds of CPU hours. The method needs a much cheaper node test before a full
run is worthwhile.

The executed source is `executed-source-v1.0.0.txt` (SHA256
`ae82bb7f9c260cdba2d3d052a46f737a2879c82636cb7257d0c1789a8581502d`); `tree.py`
differs only by its filled header hash. The tree stream is ignored scratch at
`experiments/scratch/circulant-link-lp-tree-pilot-v1.0.0/profile-0/`, SHA256
`11562c51a3d096dcfab577b6b8af66aceb0afacfc5300d633a9bd89183d805e0`.
No profile is excluded by this pilot.
