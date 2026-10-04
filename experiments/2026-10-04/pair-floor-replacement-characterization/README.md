```
Document:    Pair-Floor One-Block Replacement Characterization
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      93e1b172e38cd69d9824eb065646514b54a337f32379039f91c42f37a8129956
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Pair-floor one-block replacements

For the fixed H12/D2=32 family, the forced-endpoint rule exactly matches a fresh pair recount for all **275,456** replacements of one incumbent block by one of the 4,304 blocks outside the incumbent. There were no disagreements. No objective was computed, no family was ranked, and no solver was called.

## Exact condition and proof

Let F be a family whose pair multiplicities are all at least five. Remove a block B in F and add a block A outside F. Let E(B) be the pairs contained in B whose multiplicity in F is exactly five. Define S(B) as the union of the endpoints of the pairs in E(B).

The replacement preserves the pair floor if and only if **S(B) is a subset of A**.

For every point pair P, its new count is `c(P) - 1[P subset B] + 1[P subset A]`. If P is outside B, its count cannot fall. If P is in B and its old count is at least six, its new count is still at least five. The remaining pairs are exactly E(B): each drops to four unless A contains it. Thus every pair in E(B) must be contained in A, and that condition is sufficient. Containing every such pair is equivalent to containing their union of endpoints S(B). The proof concerns the pair floor alone.

For `s = |S(B)|`, the number of allowed added blocks is exactly `C(16-s, 5-s) - #{D in F : S(B) subset D}`. The first term lists all five-point supersets of S(B); the second removes the incumbent blocks, including B. Each ordered choice `(B,A)` gives a distinct neighboring family because its removed and added blocks are recoverable by set differences.

## Counts for this fixed family

| Forced points s | Removed blocks | Allowed replacements |
|---:|---:|---:|
| 0 | 2 | 8,608 |
| 1 | 0 | 0 |
| 2 | 0 | 0 |
| 3 | 1 | 76 |
| 4 | 6 | 66 |
| 5 | 55 | 0 |
| Total | 64 | 8,750 |

The two removals with no forced points are `{1,5,6,8,11}` and `{2,5,6,7,8}`. Every pair in either block has multiplicity at least six in the incumbent. Each of these removals accepts all 4,304 outside added blocks under the pair-floor test. Consequently all 4,304 outside blocks occur in some pair-floor-legal replacement.

Removing `{2,7,8,9,15}` forces `{2,8,15}` and permits 76 outside additions. Each of the six four-point forced sets permits eleven additions. For each of the other 55 removals, all five points are forced; the only possible five-point superset is the removed block itself, which is excluded as an incumbent block.

## Independent enumeration and scope

The checker freshly counts the remaining 63 blocks for every removal. For each outside added block, it copies those counts, adds its ten pairs, and tests all 120 pair counts. It compares that result with both the critical-pair and forced-endpoint conditions and checks the counting formula. Per-removal direct and forced bitmaps have matching hashes. Deliberately omitting each required endpoint supplies a recorded counterexample to the damaged reduction; malformed input controls are rejected.

Both package and standalone verifiers confirm that the fixed input has 64 distinct blocks and 12 holes. The input SHA256 is `cadb86e4f2243eada269dc314bca0bc5c238f5b0ca2bd9525dd0b67aad24c970`. Point labels and block IDs retain the existing conventions.

The 8,750 replacements satisfy only the pair floor. This does not establish single-triple, quadruple, stronger-row, core-cap, or covering validity. These counts apply to one replacement of this fixed incumbent. They do not justify restrictions on multiblock or unrestricted search, and they establish no global covering-number bound.
