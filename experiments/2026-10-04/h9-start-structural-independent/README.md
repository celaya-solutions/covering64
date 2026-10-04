```text
Document:    Independent H9 Structural and Radius-Four Certificate Review
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      f2893e2cc8ca812fd0d006fb128d1c7e18c35e2a4fb13b9f5d7cd013cebd648b
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent H9 structural and radius-four certificate review

**PASS.** The producer certificate is bound by SHA256 `317797810b797e341ce62992334a8816e46e9051d33d41ab60c8078e0ee15d38`. The independent checker imports neither its producer nor a solver. It reconstructs the entire 4,368-block universe and the 560 triples from labels 1 through 16 in lexicographic order. Twenty-three certificate fields were independently recounted; 22 damaged-certificate or malformed-family controls were rejected. The new checker passes Ruff.

## Verified mathematical scope

The starting family is the exact 64-block partial `f5f24d57738763380c715769eef4328d7f1950a8ae6d0eedd8e9ff16dc3fc681`, with 9 uncovered triples and maximum triple multiplicity 3. Its two saved verifier outputs are hash checked and agree that it is not a cover.

Each of the four old 60-block cores has five sixfold triples whose six-block carrier sets are disjoint. In every relabeling, the starting family can contain at most 3 blocks from each such carrier set. It can share at most the remaining 30 blocks plus 15 carrier blocks, hence **at most 45 blocks with every relabeling of each old 60-block core**. This statement describes the starting partial. It is not a general upper bound on intersections of arbitrary covers.

The whole-universe hole-carrier histogram is `{0:3716,1:605,2:44,3:3}`. The three blocks covering three original holes share the hole `(5,9,15)`. Independent reachability over all 28 hole masks reproduces the producer's complete layers for zero through four added blocks. A second check of all 4,060 multisets of three masks gives a maximum union of 7 holes. Thus three new blocks cannot cover the 9 original holes. The supplied distinct four-block hole-only witness covers all 9; it does not claim to repair holes created by removing old blocks.

Suppose a full 64-block cover differed from the starting family in at most 4 block replacements. It must add exactly 4 blocks, since 3 cannot cover the original holes. Each added block must cover at least 2 original holes: otherwise that block covers at most 1, while the other 3 together cover at most 7, leaving at least 1 hole. Therefore all 4 additions must come from the 47 blocks covering at least 2 original holes.

Exactly 63 starting blocks each have a triple occurring only in that original block and in none of those 47 eligible additions. Every one of those 63 blocks must remain. Together with the 4 necessary new blocks, this would require at least 67 blocks, a contradiction. Therefore **no full 64-block cover lies within 4 replacements of this named starting family**, and **every full 64-block cover overlaps this named family in at most 59 blocks**.

This is a finite radius-four exclusion and an exact 64 named-family overlap bound. It does not prove unrestricted nonexistence, exclude distance 5, classify all relabelings of the new 62-block core, or justify a fixed cap for live families of other sizes.

## Independent controls and evidence

The replay independently verifies all hole masks and DP layers, the 47 eligible addition blocks, their 192 covered triples, all 64 original private-triple lists, the 63 protected witnesses, and the one potentially removable original block. It also recounts point profiles, degree 19 links, pair and triple multiplicities, and the four old-core proofs. The four-block hole-only witness is checked directly for distinct blocks and full hole coverage.

Damaged copies change or omit holes, carrier counts, mask patterns, DP reachability, the common hole, eligible adders, restorability triples, private witnesses, forced counts, bounds, old-core heavy triples, and the hole-only witness. Boolean-for-integer damage and widened scope are rejected. Four malformed starting-family controls cover duplicate blocks, label zero, short blocks, and reversed block order. Damaged copies are checked semantically without using their file hashes as the rejection reason.

`check.py` is the reproducible independent replay; `review.json` records its result and exact certificate binding. No native search or optimizer ran. The replay uses mask reachability and does not enumerate four-adder repair tuples. A preliminary independent hole-only enumeration found a different valid four-block hole cover; it was a small arithmetic check, not a complete repair search or cover witness.
