```text
Document:    Independent Saved Partial Common-Core Inventory
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      9b89bbb5d939aebe65eaa6e834f71bb71007901241efa1dae64e04704c8d23d7
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Saved partials under the common-core cap

One previously saved family passes the four old named-core caps, the new common-62 cap, and all weak pair rules together. It is an existing H11/D27 family from `native-variable-partial-start/seed-2026104802/search-record-5-admissible64.txt`, also saved as `search-record-4-raw64.txt`. It is not a new search result or a new best hole count.

Its canonical SHA256 is `439d5153ba2f2063c8dedb20ce71f9381dfecdca087e4fa9f9f0dd3808f4d22f`. Fresh independent recount and both covering verifiers agree on 64 distinct blocks and 11 missing triples. Its D2max and D2sum are 27, minimum pair count is five, D3 and D4 are zero, old named-core overlaps are [1,1,0,1], and common-62 overlap is zero. The canonical witness is saved as `family-439d5153ba2f2063.txt`.

The input snapshot contains 1,170 text files under the two saved experiment dates, excluding this output folder. Of these, 951 were canonical exact-64 witnesses; 420 file references had at most 11 missing triples, representing 205 distinct families. The other 219 inputs were outside the canonical exact-64 format; 531 exact-64 references had more than 11 holes. This is a frozen text-file inventory, not a claim about unrecorded families, ignored scratch archives, JSON-only witnesses, or every possible family.

Among the 205 distinct low-hole families, 45 pass all five named-core caps, 30 pass the weak pair rules, and exactly one passes both. Their hole-count histogram is H3:8, H5:25, H6:44, H7:18, H8:46, H9:13, H10:15, H11:36. The old H9 is among the five-cap passes but fails weak rules: pair minimum four, D3=104, D4=96. The old H10 likewise fails weak rules: pair minimum four, D3=78, D4=74. Raw low-hole records must remain distinct from weak-qualified records.

The recorded H11/D25 common-core bank is excluded by its common-62 overlap of 62. Every cap in this inventory is applied only to exact-64 families; the common-core cap is 56 while each old named-core cap is 55. The independently frozen common-core proof is referenced by certificate SHA256 `1006dc7a15b515c075311da4ef8f074d92da60d10ed9fe3b12db23c77dc687ad`. This inventory consumes that proof and does not establish it anew.

`inventory.json` SHA256 is `720e1856a16aaf32b3fbf456a37e644d626a849aa0ae5e3bd7b989bd6680cece`. It retains all selected IDs, metrics, witnesses, and source paths with hashes. `inputs.json` freezes every examined text path and source hash. Six damaged controls (duplicate, wrong cardinality, zero label, float label, Boolean label, and unsorted blocks) were rejected. All 205 selected families were freshly recounted and checked by both covering verifiers. No cover was found, and no optimizer, native query, or neighborhood search was launched.

To reproduce only this finite audit, run `uv run python experiments/2026-10-04/h11-common-core-saved-inventory-independent/check.py`. Existing input bytes are hash checked and the original input snapshot is reused. The result does not settle unrestricted C(16,5,3) existence or establish a global lower bound.
