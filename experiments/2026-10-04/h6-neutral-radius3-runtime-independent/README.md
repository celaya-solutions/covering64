# Neutral three-block runtime audit

~~~text
Document:    H6 Neutral Radius-Three Runtime Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      0449bd51d72d7dd6dcb678b58e80bddcc35657d478da995c0ad89e12bca24503
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
~~~

The root-launched neutral search completed all three shells in 0.289718 native
seconds with no timeout or watchdog action. It checked 64, 2,016, and 41,664
deletion sets and exactly 3, 1,043, and 185,917 addition tuples, matching the
checked screen. Exactly three non-original families were found. All occur at
distance one; no candidates occur at distances two or three.

The runtime audit rehashed all 178 pins and the independent gate, compared
receipts and raw output, and checked every native and saved witness. It
independently ran both verifiers and recounted the pair, triple, quadruple, and
six named-core classifications for all three candidates. All saved verifier
receipts agree. No search was rerun.

## The three endpoints

Every candidate removes the same block (4,5,9,14,16), global ID 3209.

| Candidate SHA256 prefix | Added block | Added ID | Low-degree point moved to |
| --- | --- | ---: | ---: |
| 7746887b0f7c | (4,5,6,9,14) | 3102 | 16 |
| 688b0e7a142d | (4,5,6,9,16) | 3104 | 14 |
| f7a82e5ea0ba | (4,5,6,14,16) | 3124 | 9 |

All three have the same measured scores as the original: H6, minimum pair count
four, D2max 14, D2sum 498, D3 80, and D4 72. All pass the six named caps and fail
endpoint weak qualification. Their triple histogram remains {1:476, 2:70, 3:8};
their point-degree histogram remains {19:3, 20:10, 21:3}. The changes move the
three-hole local pattern and the two pair deficits through point six to another
point. They do not improve the measured deficits.

The four families share 63 blocks and are pairwise at distance one. A neutral
search of radius two from any of the new families cannot discover another
family: the triangle inequality puts it inside the original, completely
enumerated neutral radius three.

## Strict-search assessment

No candidate has a demonstrated score advantage for a strict four-block search.
A strict search of radius at most three from any cannot improve the hole count,
because it stays inside the original, separately checked strict radius four.
A strict four-block improvement from one of them would necessarily be at
distance five from the original family.

More precisely, let B0 be the removed original block and Bi the new block. Any
such exact64 improvement must retain Bi and omit B0; otherwise its overlap with
the original would be at least 60, contradicting the completed strict-radius-four
exclusion. Its four removed blocks would therefore come from the shared63 core.
This observation is a consequence of the existing local results, not a new search.

The three candidates remain usable exploratory centers, but there is no measured
reason to favor one. Enlarging the original neutral neighborhood is a more
direct way to look for a new H6 center than repeating the now-closed small
neighborhoods. No additional production search is launched by this audit.
